/*
 * Header file for: Controller
 * Generated with : PLECS 5.0.6
 *                  TI28P55x 2.3.3
 * Generated on   : 11 Nov 2026 16:56:06
 */
#ifndef PLECS_HEADER_Controller_h_
#define PLECS_HEADER_Controller_h_

#include <stdbool.h>
#include <stdint.h>

/* Target typedefs */
typedef int_fast8_t int8_t;
typedef uint_fast8_t uint8_t;


/* Model floating point type */
typedef float Controller_FloatType;

/* Target declarations */
extern void Controller_background(void);
#pragma diag_suppress 552


/* Model checksum */
extern const char * const Controller_checksum;

/* Model error status */
extern const char * Controller_errorStatus;


/* Model sample time */
extern const float Controller_sampleTime;


/* Block outputs */
typedef struct
{
   float PB_controller[12];         /* Controller/PB_controller */
   float enableswitch;              /* Controller/enableswitch */
   float ADC_A[2];                  /* Controller/ADC_A */
   float ADC_B[2];                  /* Controller/ADC_B */
   float Load[5];                   /* Controller/Load */
} Controller_BlockOutputs;
extern Controller_BlockOutputs Controller_B;

#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
/* External mode signals */
#define Controller_NumExtModeSignals 10
extern const float * const Controller_ExtModeSignals[];
/* Tunable parameters */
#define Controller_NumTunableParameters 8
#endif /* defined(EXTERNAL_MODE) */


/* Block parameters */
typedef struct
{
   /* Parameter 'SwitchState' of
    *  Manual Signal Switch : 'Controller/enableswitch'
    */
   bool enableswitch_SwitchState;
   /* Parameter 'Value' of
    *  Constant : 'Controller/Vref_rms'
    */
   float Vref_rms_Value;
   /* Parameter 'Value' of
    *  Constant : 'Controller/Kp'
    */
   float Kp_Value;
   /* Parameter 'Value' of
    *  Constant : 'Controller/Ki'
    */
   float Ki_Value;
   /* Parameter 'Value' of
    *  Constant : 'Controller/FF'
    */
   float FF_Value;
   /* Parameter 'Value' of
    *  Constant : 'Controller/Trip_vo'
    */
   float Trip_vo_Value;
   /* Parameter 'Value' of
    *  Constant : 'Controller/Trip_iL'
    */
   float Trip_iL_Value;
   /* Parameter 'Value' of
    *  Constant : 'Controller/Trip_io'
    */
   float Trip_io_Value;
} Controller_Parameters;
extern Controller_Parameters Controller_P;

/* Entry point functions */
void Controller_initialize(void);
void Controller_step(void);
void Controller_terminate(void);

#endif /* PLECS_HEADER_Controller_h_ */
