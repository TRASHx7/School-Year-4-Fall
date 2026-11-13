/*
 * Implementation file for: Controller
 * Generated with         : PLECS 5.0.6
 *                          TI28P55x 2.3.3
 * Generated on           : 11 Nov 2026 16:56:06
 */
#include "Controller.h"
#ifndef PLECS_HEADER_Controller_h_
#error The wrong header file "Controller.h" was included. Please check your
#error include path to see whether this file name conflicts with the name
#error of another header file.
#endif /* PLECS_HEADER_Controller_h_ */
#if defined(__GNUC__) && (__GNUC__ > 4)
#   define _ALIGNMENT 16
#   define _RESTRICT __restrict
#   define _ALIGN __attribute__((aligned(_ALIGNMENT)))
#   if defined(__clang__)
#      if __has_builtin(__builtin_assume_aligned)
#         define _ASSUME_ALIGNED(a) __builtin_assume_aligned(a, _ALIGNMENT)
#      else
#         define _ASSUME_ALIGNED(a) a
#      endif
#   else
#      define _ASSUME_ALIGNED(a) __builtin_assume_aligned(a, _ALIGNMENT)
#   endif
#else
#   ifndef _RESTRICT
#      define _RESTRICT
#   endif
#   ifndef _ALIGN
#      define _ALIGN
#   endif
#   ifndef _ASSUME_ALIGNED
#      define _ASSUME_ALIGNED(a) a
#   endif
#endif
#include <stdint.h>
#include <stdbool.h>
#include <math.h>
#include <string.h>
#include "plx_hal.h"
#define PLECSRunTimeError(msg) Controller_errorStatus = msg
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
static struct CScriptStruct Controller_cScriptStruct[1];
static char Controller_isMajorStep = '\001';
#define Controller_UNCONNECTED 0
void Controller_0_cScriptStart(const struct CScriptStruct *cScriptStruct);
void Controller_0_cScriptOutput(const struct CScriptStruct *cScriptStruct);
void Controller_0_cScriptUpdate(const struct CScriptStruct *cScriptStruct);
void Controller_0_cScriptDerivative(const struct CScriptStruct *cScriptStruct);
void Controller_0_cScriptTerminate(const struct CScriptStruct *cScriptStruct);
static uint32_t Controller_tickLo;
static int32_t Controller_tickHi;
Controller_BlockOutputs Controller_B;
#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
const float * const Controller_ExtModeSignals[] = {
   &Controller_B.Load[0],
   &Controller_B.PB_controller[10],
   &Controller_B.PB_controller[7],
   &Controller_B.PB_controller[9],
   &Controller_B.PB_controller[3],
   &Controller_B.PB_controller[5],
   &Controller_B.PB_controller[4],
   &Controller_B.PB_controller[11],
   &Controller_B.PB_controller[8],
   &Controller_B.PB_controller[6]
};
#endif /* defined(EXTERNAL_MODE) */
Controller_Parameters Controller_P = {
   /* Parameter 'SwitchState' of
    *  Manual Signal Switch : 'Controller/enableswitch'
    */
   false,
   /* Parameter 'Value' of
    *  Constant : 'Controller/Vref_rms'
    */
   25.f,
   /* Parameter 'Value' of
    *  Constant : 'Controller/Kp'
    */
   0.01f,
   /* Parameter 'Value' of
    *  Constant : 'Controller/Ki'
    */
   60.f,
   /* Parameter 'Value' of
    *  Constant : 'Controller/FF'
    */
   1.f,
   /* Parameter 'Value' of
    *  Constant : 'Controller/Trip_vo'
    */
   0.f,
   /* Parameter 'Value' of
    *  Constant : 'Controller/Trip_iL'
    */
   0.f,
   /* Parameter 'Value' of
    *  Constant : 'Controller/Trip_io'
    */
   0.f
};
const char * Controller_errorStatus;
const float Controller_sampleTime = 0.0001004f;
const char * const Controller_checksum =
   "e8aafbb01d6658bc09198b827612e1c3738ba6fc";
/* Target declarations */
// tag step function to allow special linking
#pragma CODE_SECTION(Controller_step, "step")
extern void Controller_initHal();

void Controller_initialize(void)
{
   Controller_tickHi = 0;
   Controller_tickLo = 0;

   /* Target pre-initialization */
   Controller_initHal();


   /* Initialization for C-Script : 'Controller/PB_controller' */
   {
      static const int numInputSignals[] = {
         12
      };
      static const float* const inputPtrs[] = {
         &Controller_B.ADC_A[0], &Controller_B.ADC_A[1],
         &Controller_B.ADC_B[0], &Controller_B.ADC_B[1],
         &Controller_B.enableswitch, &Controller_P.Vref_rms_Value,
         &Controller_P.Kp_Value, &Controller_P.Ki_Value,
         &Controller_P.FF_Value, &Controller_P.Trip_vo_Value,
         &Controller_P.Trip_iL_Value, &Controller_P.Trip_io_Value
      };
      static const float* const * const inputs[] = {
         &inputPtrs[0]
      };
      static const int numOutputSignals[] = {
         12
      };
      static float* const outputPtrs[] = {
         &Controller_B.PB_controller[0], &Controller_B.PB_controller[1],
         &Controller_B.PB_controller[2], &Controller_B.PB_controller[3],
         &Controller_B.PB_controller[4], &Controller_B.PB_controller[5],
         &Controller_B.PB_controller[6], &Controller_B.PB_controller[7],
         &Controller_B.PB_controller[8], &Controller_B.PB_controller[9],
         &Controller_B.PB_controller[10], &Controller_B.PB_controller[11]
      };
      static float* const * const outputs[] = {
         &outputPtrs[0]
      };
      static float nextSampleHit;
      static const char * const sampleHits[] = {
         &Controller_isMajorStep
      };
      static const float sampleTimePeriods[] = {
         0.0001004
      };
      static const float sampleTimeOffsets[] = {
         0
      };
      static const float terminalSampleTimePeriods[] = {
         0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f
      };
      static const float terminalSampleTimeOffsets[] = {
         -1.f, -1.f, -1.f, -1.f, -1.f, -1.f, -1.f, -1.f, -1.f, -1.f, -1.f,
         -1.f
      };
      static const float* const terminalSampleTimePeriodPtrs[] = {
         &terminalSampleTimePeriods[0]
      };
      static const float* const terminalSampleTimeOffsetPtrs[] = {
         &terminalSampleTimeOffsets[0]
      };
      static const char* errorStatus;
      static const char* warningStatus;
      static const char* rangeErrorMsg;
      static const float paramData[] = {
         166.f,0.0001004f,46.9483568f,-76.056338f,64.9350649f,-105.194805f,
         50.f,7.f,6.f,58.f,35.f,40.f,0.96f,15.f,100.f
      };
      static const float* const paramDataPtr[] = {
         paramData+0,paramData+1,paramData+2,paramData+3,paramData+4,
         paramData+5,paramData+6,paramData+7,paramData+8,paramData+9,
         paramData+10,paramData+11,paramData+12,paramData+13,paramData+14
      };
      static const char paramStringData[] = "\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0";
      static const char* const paramStringDataPtr[] = {
         paramStringData+0,paramStringData+1,paramStringData+2,
         paramStringData+3,paramStringData+4,paramStringData+5,
         paramStringData+6,paramStringData+7,paramStringData+8,
         paramStringData+9,paramStringData+10,paramStringData+11,
         paramStringData+12,paramStringData+13,paramStringData+14
      };
      static const int paramDim[] = {
         1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
      };
      static const int* const paramDimPtr[] = {
         paramDim+0,paramDim+2,paramDim+4,paramDim+6,paramDim+8,paramDim+10,
         paramDim+12,paramDim+14,paramDim+16,paramDim+18,paramDim+20,paramDim+
         22,paramDim+24,paramDim+26,paramDim+28
      };
      static const int paramNumElements[] = {
         1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
      };
      static const int paramNumDims[] = {
         2,2,2,2,2,2,2,2,2,2,2,2,2,2,2
      };
      errorStatus = NULL;
      warningStatus = NULL;
      rangeErrorMsg = NULL;
      Controller_cScriptStruct[0].isMajorTimeStep = 1;
      Controller_cScriptStruct[0].isRefineStep = 0;
      Controller_cScriptStruct[0].numInputTerminals = 1;
      Controller_cScriptStruct[0].numInputSignals = numInputSignals;
      Controller_cScriptStruct[0].inputs = inputs;
      Controller_cScriptStruct[0].numOutputTerminals = 1;
      Controller_cScriptStruct[0].numOutputSignals = numOutputSignals;
      Controller_cScriptStruct[0].outputs = outputs;
      Controller_cScriptStruct[0].numContStates = 0;
      Controller_cScriptStruct[0].contStates = NULL;
      Controller_cScriptStruct[0].contDerivs = NULL;
      Controller_cScriptStruct[0].numDiscStates = 0;
      Controller_cScriptStruct[0].discStates = NULL;
      Controller_cScriptStruct[0].numZCSignals = 0;
      Controller_cScriptStruct[0].numParameters = 15;
      Controller_cScriptStruct[0].paramNumDims = paramNumDims;
      Controller_cScriptStruct[0].paramDims = paramDimPtr;
      Controller_cScriptStruct[0].paramNumElements = paramNumElements;
      Controller_cScriptStruct[0].paramRealData = paramDataPtr;
      Controller_cScriptStruct[0].paramStringData = paramStringDataPtr;
      Controller_cScriptStruct[0].numSampleTimes = 1;
      Controller_cScriptStruct[0].sampleTimePeriods = sampleTimePeriods;
      Controller_cScriptStruct[0].sampleTimeOffsets = sampleTimeOffsets;
      Controller_cScriptStruct[0].inputSampleTimePeriods =
         terminalSampleTimePeriodPtrs;
      Controller_cScriptStruct[0].inputSampleTimeOffsets =
         terminalSampleTimeOffsetPtrs;
      Controller_cScriptStruct[0].sampleHits = sampleHits;
      Controller_cScriptStruct[0].nextSampleHit = &nextSampleHit;
      Controller_cScriptStruct[0].errorStatus = &errorStatus;
      Controller_cScriptStruct[0].warningStatus = &warningStatus;
      Controller_cScriptStruct[0].rangeErrorMsg = &rangeErrorMsg;
      Controller_0_cScriptStart(&Controller_cScriptStruct[0]);
      if (*Controller_cScriptStruct[0].errorStatus)
         Controller_errorStatus = *Controller_cScriptStruct[0].errorStatus;
   }
}

void Controller_step(void)
{
   if (Controller_errorStatus)
   {
      return;
   }

   /* ADC : 'Controller/ADC_A' */
   Controller_B.ADC_A[0] = PLXHAL_ADC_getIn(0, 0);
   Controller_B.ADC_A[1] = PLXHAL_ADC_getIn(0, 1);

   /* ADC : 'Controller/ADC_B' */
   Controller_B.ADC_B[0] = PLXHAL_ADC_getIn(1, 0);
   Controller_B.ADC_B[1] = PLXHAL_ADC_getIn(1, 1);

   /* Manual Signal Switch : 'Controller/enableswitch'
    * incorporates
    *  Constant : 'Controller/enable'
    *  Constant : 'Controller/disable'
    */
   Controller_B.enableswitch =
      Controller_P.enableswitch_SwitchState ? 1.f : 0.f;

   /* C-Script : 'Controller/PB_controller' */
   Controller_0_cScriptOutput(&Controller_cScriptStruct[0]);
   if (*Controller_cScriptStruct[0].errorStatus)
      Controller_errorStatus = *Controller_cScriptStruct[0].errorStatus;

   /* CPU Load : 'Controller/Load' */
   Controller_B.Load[0] = PLXHAL_DISPR_getTask0LoadInPercent();
   Controller_B.Load[1] = PLXHAL_DISPR_getTimeStamp0();
   Controller_B.Load[2] = PLXHAL_DISPR_getTimeStampB();
   Controller_B.Load[3] = PLXHAL_DISPR_getTimeStampD();
   Controller_B.Load[4] = PLXHAL_DISPR_getTimeStampP();

   /* Powerstage Protection : 'Controller/Protection' */
   if((Controller_B.PB_controller[2]) > 0)
   {
      PLXHAL_PWR_setEnableRequest(true);
   }
   else
   {
      PLXHAL_PWR_setEnableRequest(false);
   }
   /* PWM : 'Controller/PWM' */

   PLXHAL_PWM_setDuty(0, Controller_B.PB_controller[0]);
   /* PWM : 'Controller/PWM1' */

   PLXHAL_PWM_setDuty(1, Controller_B.PB_controller[1]);
   if (Controller_errorStatus)
   {
      return;
   }

   /* Update for C-Script : 'Controller/PB_controller' */
   Controller_0_cScriptUpdate(&Controller_cScriptStruct[0]);
   if (*Controller_cScriptStruct[0].errorStatus)
      Controller_errorStatus = *Controller_cScriptStruct[0].errorStatus;

   /* Update for PWM : 'Controller/PWM' */
   PLXHAL_PWR_syncdPwmEnable();
}

void Controller_terminate(void)
{
   /* Target termination */
#pragma diag_default 552

   /* Termination for C-Script : 'Controller/PB_controller' */
   Controller_0_cScriptTerminate(&Controller_cScriptStruct[0]);
   if (*Controller_cScriptStruct[0].errorStatus)
      Controller_errorStatus = *Controller_cScriptStruct[0].errorStatus;
}
