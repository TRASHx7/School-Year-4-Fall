/*
 * C-Script file for: Controller/PB_controller
 * Generated with   : PLECS 5.0.6
 * Generated on     : 11 Nov 2026 16:56:06
 */
typedef float real_t;
#define REAL_MAX FLT_MAX
#define REAL_MIN FLT_MIN
#define REAL_EPSILON FLT_EPSILON
/*
 * ENEL 585 Fall 2026, Project B: single-phase standalone inverter controller.
 * Group 8 (Station 5 per the Oct 29 list).
 *
 * This file is the single source of the controller. It is pasted (by gen_plecs.py) into the
 * "Declarations" section of the C-Script block in both PLECS models, and it is compiled
 * unchanged by design/simulate.py for the switched simulation. Do not edit the copies inside
 * the .plecs files; edit this file and regenerate.
 *
 * Control law (one call per PWM carrier period, sampled at the carrier valley):
 *   theta_k  = 2 pi k / N, N = carrier periods per 60 Hz period (table based, synchronous)
 *   vref     = A sin(theta_k)                       A = sqrt(2) Vref_rms (soft start, then steps
 *                                                   applied at the positive zero crossing)
 *   e        = vref - vo
 *   xd, xq  += 2 Ki Ts e sin(theta), 2 Ki Ts e cos(theta)      (resonant term, see below)
 *   u_r      = xd sin(theta) + xq cos(theta)
 *   v*       = FF vref + Kp e + u_r
 *   m        = v* / vdc,  |m| <= M_MAX
 *   dA = (1 + m)/2, dB = (1 - m)/2                  (unipolar SPWM: both legs, same carrier)
 *
 * The pair (xd, xq) is the ideal resonant term of Lecture 11: demodulate, integrate, remodulate
 * gives u_r(t) = 2 Ki * integral e(t') cos(w1 (t - t')) dt', whose Laplace transform is
 * 2 Ki s / (s^2 + w1^2). Because sin and cos come from the same table as the reference, the
 * resonance sits exactly on the reference frequency, with no drift in single precision.
 * Anti-windup: the correction amplitude sqrt(xd^2 + xq^2) is clamped to X_MAX.
 *
 * Protection (latched, PWM off, cleared only by setting enableswitch to 0). The vo, iL and io
 * levels can be lowered live for HIL tests (Trip_vo, Trip_iL, Trip_io), never raised:
 *   bit 0  |vo|  > TRIP_VO        bit 3  vdc > TRIP_VDC_HI
 *   bit 1  |iL|  > TRIP_IL        bit 4  vdc < TRIP_VDC_LO while running
 *   bit 2  |io|  > TRIP_IO        bit 5  vo polarity opposite to vref during soft start
 */

#include <math.h>

#define PB_MAX_N 512

typedef struct
{
   /* fixed parameters (C-Script "Parameters" or the test harness) */
   int N;               /* table length = carrier periods per fundamental period */
   float Ts;            /* control period, s */
   float v_scale, v_offset;    /* voltage channel: x = scale * Vpin + offset */
   float i_scale, i_offset;    /* current channel */
   float trip_vo, trip_il, trip_io, trip_vdc_hi, trip_vdc_lo;
   float vdc_start_min;
   float m_max;
   float x_max;
   float ramp_rate;     /* V/s of peak amplitude during soft start */
} pb_param_t;

typedef struct
{
   /* measured pin voltages (V), in this order on the C-Script input */
   float vpin_vdc, vpin_il, vpin_vo, vpin_io;
   /* operator inputs (tunable constants in the model) */
   float enable;        /* enableswitch: 0 off, 1 on */
   float vref_rms;      /* output voltage reference, V rms */
   float kp;            /* proportional gain */
   float ki;            /* resonant gain, 1/s */
   float ff;            /* reference feedforward gain (1 on, 0 off) */
   /* test thresholds: can only LOWER the trips below the fixed design values (0 = use design) */
   float trip_vo_set, trip_il_set, trip_io_set;
} pb_in_t;

typedef struct
{
   float dA, dB;        /* duty of leg A (ePWM1) and leg B (ePWM2), 0..1 */
   float pwm_en;        /* to the Powerstage Protection block */
   float fault;         /* latched fault bits */
   float amp;           /* present reference amplitude, V peak */
   float m;             /* modulation index after the limit */
   float x_amp;         /* resonant correction amplitude, V */
   float vref;          /* instantaneous reference, V */
   float vdc, il, vo, io;    /* measurements in physical units */
} pb_out_t;

#define PB_NUM_OUTPUTS 12

typedef struct
{
   int k;               /* table index 0..N-1 */
   int run;             /* 1 while switching */
   int soft;            /* 1 during soft start */
   int fault;           /* latched fault bits */
   float amp;           /* reference amplitude now */
   float xd, xq;        /* resonant states */
   float pol_acc;       /* polarity check accumulator over one cycle */
} pb_state_t;

static float pb_sin[PB_MAX_N];
static float pb_cos[PB_MAX_N];

static void pb_init(pb_state_t *s, const pb_param_t *p)
{
   int n;
   int N = p->N;
   if (N > PB_MAX_N)
      N = PB_MAX_N;
   for (n = 0; n < N; n++)
   {
      pb_sin[n] = (float)sin(6.283185307179586 * n / N);
      pb_cos[n] = (float)cos(6.283185307179586 * n / N);
   }
   s->k = 0;
   s->run = 0;
   s->soft = 0;
   s->fault = 0;
   s->amp = 0.0f;
   s->xd = 0.0f;
   s->xq = 0.0f;
   s->pol_acc = 0.0f;
}

static float pb_absf(float x)
{
   return x < 0.0f ? -x : x;
}

/* One control step. Reads *s, writes the outputs to *o and the next state to *ns.
 * Pure function of (input, state), so it can be called from both the output and the update
 * function of the C-Script without double-updating the state. */
static void pb_step(const pb_in_t *in, const pb_state_t *s,
                    const pb_param_t *p,
                    pb_out_t *o, pb_state_t *ns)
{
   int N = p->N > PB_MAX_N ? PB_MAX_N : p->N;
   int k = s->k;
   float sn, cs, vdc, il, vo, io, target, vref, e, ur, vstar, m, den, xa, sc,
         xlim;
   float t_vo, t_il, t_io;
   int trip = 0;

   *ns = *s;

   /* measurements in physical units */
   vdc = p->v_scale * in->vpin_vdc + p->v_offset;
   il  = p->i_scale * in->vpin_il  + p->i_offset;
   vo  = p->v_scale * in->vpin_vo  + p->v_offset;
   io  = p->i_scale * in->vpin_io  + p->i_offset;

   sn = pb_sin[k];
   cs = pb_cos[k];

   /* ---------------- protection: always armed ---------------- */
   /* tunable test thresholds may lower a trip, never raise it */
   t_vo =
      (in->trip_vo_set > 0.0f && in->trip_vo_set <
       p->trip_vo) ? in->trip_vo_set : p->trip_vo;
   t_il =
      (in->trip_il_set > 0.0f && in->trip_il_set <
       p->trip_il) ? in->trip_il_set : p->trip_il;
   t_io =
      (in->trip_io_set > 0.0f && in->trip_io_set <
       p->trip_io) ? in->trip_io_set : p->trip_io;
   if (pb_absf(vo) > t_vo)
      trip |= 1;
   if (pb_absf(il) > t_il)
      trip |= 2;
   if (pb_absf(io) > t_io)
      trip |= 4;
   if (vdc > p->trip_vdc_hi)
      trip |= 8;
   if (s->run && vdc < p->trip_vdc_lo)
      trip |= 16;
   ns->fault = s->fault | trip;

   /* fault is acknowledged only by switching enable off */
   if (in->enable < 0.5f)
   {
      ns->fault = 0;
   }

   /* ---------------- run / stop ---------------- */
   if (in->enable < 0.5f || ns->fault)
   {
      ns->run = 0;
      ns->soft = 0;
      ns->amp = 0.0f;
      ns->xd = 0.0f;
      ns->xq = 0.0f;
      ns->pol_acc = 0.0f;
   }
   else if (!s->run)
   {
      /* start at a positive-going zero crossing of the reference, with enough DC link */
      if (k == 0 && vdc > p->vdc_start_min)
      {
         ns->run = 1;
         ns->soft = 1;
         ns->amp = 0.0f;
         ns->pol_acc = 0.0f;
      }
   }

   /* ---------------- reference amplitude ---------------- */
   target = 1.41421356f * in->vref_rms;
   if (target < 0.0f)
      target = 0.0f;
   if (target > p->trip_vo * 0.98f)
      target = p->trip_vo * 0.98f;

   if (ns->run)
   {
      if (ns->soft)
      {
         /* first step after the start: amp stays 0; then ramp at ramp_rate */
         ns->amp = s->run ? s->amp + p->ramp_rate * p->Ts : 0.0f;
         if (ns->amp >= target)
         {
            ns->amp = target;
            ns->soft = 0;
         }
         /* polarity check: vo must be in phase with vref once the amplitude is a few volts */
         ns->pol_acc = s->pol_acc + vo * sn;
         if (k == N - 1)
         {
            if (s->amp > 2.0f && ns->pol_acc < 0.0f)
               ns->fault |= 32;
            ns->pol_acc = 0.0f;
         }
         if (ns->fault)
         {
            ns->run = 0;
            ns->soft = 0;
            ns->amp = 0.0f;
         }
      }
      else if (k == 0)
      {
         ns->amp = target;      /* reference steps take effect at the zero crossing */
      }
      else
      {
         ns->amp = s->amp;
      }
   }

   vref = ns->amp * sn;
   e = vref - vo;

   /* ---------------- resonant term (ideal R, Lecture 11) with anti-windup ---------------- */
   if (ns->run && !ns->fault)
   {
      float g = 2.0f * in->ki * p->Ts * e;
      ns->xd = s->xd + g * sn;
      ns->xq = s->xq + g * cs;
      /* with feedforward off, the resonant term must supply the whole output */
      xlim = p->x_max + (1.0f - in->ff) * 1.2f * target;
      xa = sqrtf(ns->xd * ns->xd + ns->xq * ns->xq);
      if (xa > xlim)
      {
         sc = xlim / xa;
         ns->xd *= sc;
         ns->xq *= sc;
         xa = xlim;
      }
   }
   else
   {
      ns->xd = 0.0f;
      ns->xq = 0.0f;
      xa = 0.0f;
   }
   ur = ns->xd * sn + ns->xq * cs;

   /* ---------------- modulation ---------------- */
   vstar = in->ff * vref + in->kp * e + ur;
   den = vdc > 10.0f ? vdc : 10.0f;
   m = vstar / den;
   if (m > p->m_max)
      m = p->m_max;
   if (m < -p->m_max)
      m = -p->m_max;

   if (ns->run && !ns->fault)
   {
      o->dA = 0.5f + 0.5f * m;
      o->dB = 0.5f - 0.5f * m;
      o->pwm_en = 1.0f;
   }
   else
   {
      o->dA = 0.5f;
      o->dB = 0.5f;
      o->pwm_en = 0.0f;
      m = 0.0f;
   }

   o->fault = (float)ns->fault;
   o->amp = ns->amp;
   o->m = m;
   o->x_amp = xa;
   o->vref = vref;
   o->vdc = vdc;
   o->il = il;
   o->vo = vo;
   o->io = io;

   ns->k = (k + 1 >= N) ? 0 : k + 1;
}

/* ---- C-Script glue (generated by gen_plecs.py) ---- */
static pb_param_t pbP;
static pb_state_t pbS, pbNext;
static pb_in_t pbIn;
static pb_out_t pbOut;
#define PRM(i) ((float)ParamRealData(i, 0))

struct CScriptStruct
{
   int numInputTerminals;
   int numOutputTerminals;
   const int* numInputSignals;
   const int* numOutputSignals;
   int numContStates;
   int numDiscStates;
   int numZCSignals;
   int numSampleTimes;
   int numParameters;
   int isMajorTimeStep;
   int isRefineStep;
   float time;
   const float * const * const *inputs;
   float * const * const *outputs;
   float *contStates;
   float *contDerivs;
   float *discStates;
   float *zCSignals;
   const int *paramNumDims;
   const int * const *paramDims;
   const int *paramNumElements;
   const float * const *paramRealData;
   const char * const *paramStringData;
   const char * const *sampleHits;
   const float *sampleTimePeriods;
   const float *sampleTimeOffsets;
   const float * const *inputSampleTimePeriods;
   const float * const *inputSampleTimeOffsets;
   float *nextSampleHit;
   const char** errorStatus;
   const char** warningStatus;
   const char** rangeErrorMsg;
   int* rangeErrorLine;
   void (*writeCustomStateDouble)(void*, float);
   float (*readCustomStateDouble)(void*);
   void (*writeCustomStateInt)(void*, int);
   void (*writeCustomStateData)(void*, const void*, int);
   void (*readCustomStateData)(void*, void*, int);
};
#define NumInputs cScriptStruct->numInputSignals[0]
#define NumOutputs cScriptStruct->numOutputSignals[0]
#define Input(signalIdx) (*cScriptStruct->inputs[0][signalIdx])
#define Output(signalIdx) (*cScriptStruct->outputs[0][signalIdx])
#define NumInputTerminals cScriptStruct->numInputTerminals
#define NumOutputTerminals cScriptStruct->numOutputTerminals
#define NumInputSignals(terminalIdx) cScriptStruct->numInputSignals[ \
      terminalIdx]
#define NumOutputSignals(terminalIdx) cScriptStruct->numOutputSignals[ \
      terminalIdx]
#define InputSignal(terminalIdx, \
                    signalIdx) (*cScriptStruct->inputs[terminalIdx][signalIdx])
#define OutputSignal(terminalIdx, \
                     signalIdx) (*cScriptStruct->outputs[terminalIdx][ \
                                    signalIdx])
#define NumContStates cScriptStruct->numContStates
#define NumDiscStates cScriptStruct->numDiscStates
#define NumZCSignals cScriptStruct->numZCSignals
#define NumParameters cScriptStruct->numParameters
#define NumSampleTimes cScriptStruct->numSampleTimes
#define IsMajorStep cScriptStruct->isMajorTimeStep
#define IsRefineStep cScriptStruct->isRefineStep
#define CurrentTime cScriptStruct->time
#define NextSampleHit (*cScriptStruct->nextSampleHit)
#define SetErrorMessage(string) { *cScriptStruct->errorStatus=(string); }
#define SetWarningMessage(string)
#define ContState(idx) cScriptStruct->contStates[idx]
#define ContDeriv(idx) cScriptStruct->contDerivs[idx]
#define DiscState(idx) cScriptStruct->discStates[idx]
#define ZCSignal(idx) cScriptStruct->zCSignals[idx]
#define IsSampleHit(idx) (*cScriptStruct->sampleHits[idx])
#define SampleTimePeriod(idx) cScriptStruct->sampleTimePeriods[idx]
#define SampleTimeOffset(idx) cScriptStruct->sampleTimeOffsets[idx]
#define InputSampleTimePeriod(terminalIdx, \
                              signalIdx) cScriptStruct->inputSampleTimePeriods \
   [terminalIdx][signalIdx]
#define InputSampleTimeOffset(terminalIdx, \
                              signalIdx) cScriptStruct->inputSampleTimeOffsets \
   [terminalIdx][signalIdx]
#define ParamNumDims(idx) cScriptStruct->paramNumDims[idx]
#define ParamDim(pIdx, dIdx) cScriptStruct->paramDims[pIdx][dIdx]
#define ParamRealData(pIdx, dIdx) cScriptStruct->paramRealData[pIdx][dIdx]
#define ParamStringData(pIdx) cScriptStruct->paramStringData[pIdx]

void Controller_0_cScriptStart(const struct CScriptStruct *cScriptStruct)
{
   pbP.N = (int)(ParamRealData(0, 0) + 0.5);
   pbP.Ts = PRM(1);
   pbP.v_scale = PRM(2);
   pbP.v_offset = PRM(3);
   pbP.i_scale = PRM(4);
   pbP.i_offset = PRM(5);
   pbP.trip_vo = PRM(6);
   pbP.trip_il = PRM(7);
   pbP.trip_io = PRM(8);
   pbP.trip_vdc_hi = PRM(9);
   pbP.trip_vdc_lo = PRM(10);
   pbP.vdc_start_min = PRM(11);
   pbP.m_max = PRM(12);
   pbP.x_max = PRM(13);
   pbP.ramp_rate = PRM(14);
   pb_init(&pbS, &pbP);
   pbNext = pbS;
}

void Controller_0_cScriptOutput(const struct CScriptStruct *cScriptStruct)
{
   pbIn.vpin_vdc = (float)Input(0);
   pbIn.vpin_il = (float)Input(1);
   pbIn.vpin_vo = (float)Input(2);
   pbIn.vpin_io = (float)Input(3);
   pbIn.enable = (float)Input(4);
   pbIn.vref_rms = (float)Input(5);
   pbIn.kp = (float)Input(6);
   pbIn.ki = (float)Input(7);
   pbIn.ff = (float)Input(8);
   pbIn.trip_vo_set = (float)Input(9);
   pbIn.trip_il_set = (float)Input(10);
   pbIn.trip_io_set = (float)Input(11);
   pb_step(&pbIn, &pbS, &pbP, &pbOut, &pbNext);
   Output(0) = pbOut.dA;
   Output(1) = pbOut.dB;
   Output(2) = pbOut.pwm_en;
   Output(3) = pbOut.fault;
   Output(4) = pbOut.amp;
   Output(5) = pbOut.m;
   Output(6) = pbOut.x_amp;
   Output(7) = pbOut.vref;
   Output(8) = pbOut.vdc;
   Output(9) = pbOut.il;
   Output(10) = pbOut.vo;
   Output(11) = pbOut.io;
}

void Controller_0_cScriptUpdate(const struct CScriptStruct *cScriptStruct)
{
   pbS = pbNext;
}

void Controller_0_cScriptDerivative(const struct CScriptStruct *cScriptStruct)
{
}

void Controller_0_cScriptTerminate(const struct CScriptStruct *cScriptStruct)
{
}
