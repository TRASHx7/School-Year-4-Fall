/*
 * Header file for: tut5_PLECS_20261103
 * Generated with : PLECS 4.9.9
 *                  TI28P55x 2.2.3
 * Generated on   : 2 Nov 2026 12:47:56
 */
#ifndef PLECS_HEADER_tut5_PLECS_20261103_h_
#define PLECS_HEADER_tut5_PLECS_20261103_h_

#include <stdbool.h>
#include <stdint.h>

/* Target typedefs */
typedef int_fast8_t int8_t;
typedef uint_fast8_t uint8_t;


/* Model floating point type */
typedef float tut5_PLECS_20261103_FloatType;

/* Target declarations */
extern void tut5_PLECS_20261103_background(void);
#pragma diag_suppress 552


/* Model checksum */
extern const char * const tut5_PLECS_20261103_checksum;

/* Model error status */
extern const char * tut5_PLECS_20261103_errorStatus;


/* Model sample time */
extern const float tut5_PLECS_20261103_sampleTime;


/*
 * Model states */
typedef struct
{
   float RGain[2];                  /* tut5_PLECS_20261103/R gain */
} tut5_PLECS_20261103_ModelStates;
extern tut5_PLECS_20261103_ModelStates tut5_PLECS_20261103_X;


/* Block outputs */
typedef struct
{
   float Saturation;                /* tut5_PLECS_20261103/Saturation */
   float Saturation1;               /* tut5_PLECS_20261103/Saturation1 */
   float Load[5];                   /* tut5_PLECS_20261103/Load */
   float ADC1[2];                   /* tut5_PLECS_20261103/ADC1 */
   float ADC2;                      /* tut5_PLECS_20261103/ADC2 */
   float SineWave;                  /* tut5_PLECS_20261103/Sine Wave */
   float Subtract;                  /* tut5_PLECS_20261103/Subtract */
   float Gain;                      /* tut5_PLECS_20261103/Gain */
} tut5_PLECS_20261103_BlockOutputs;
extern tut5_PLECS_20261103_BlockOutputs tut5_PLECS_20261103_B;

#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
/* External mode signals */
#define tut5_PLECS_20261103_NumExtModeSignals 4
extern const float * const tut5_PLECS_20261103_ExtModeSignals[];
/* Tunable parameters */
#define tut5_PLECS_20261103_NumTunableParameters 4
#endif /* defined(EXTERNAL_MODE) */


/* Block parameters */
typedef struct
{
   /* Parameter 'Value' of
    *  Constant : 'tut5_PLECS_20261103/enable'
    */
   float enable_Value;
   /* Parameter 'Value' of
    *  Constant : 'tut5_PLECS_20261103/iL_ref'
    */
   float iL_ref_Value;
   /* Parameter 'Value' of
    *  Constant : 'tut5_PLECS_20261103/Kp'
    */
   float Kp_Value;
   /* Parameter 'Value' of
    *  Constant : 'tut5_PLECS_20261103/Kr'
    */
   float Kr_Value;
} tut5_PLECS_20261103_Parameters;
extern tut5_PLECS_20261103_Parameters tut5_PLECS_20261103_P;

/* Entry point functions */
void tut5_PLECS_20261103_initialize(void);
void tut5_PLECS_20261103_step(void);
void tut5_PLECS_20261103_terminate(void);

#endif /* PLECS_HEADER_tut5_PLECS_20261103_h_ */
