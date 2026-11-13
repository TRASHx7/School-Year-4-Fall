/*
 * Hardware configuration file for: TI28P55x
 * Generated with                 : PLECS 5.0.6
 * Generated on                   : Wed Nov 11 16:56:06 2026
 */

/* HAL Includes */
#include "Controller.h"
#include "plx_hal.h"
#include "plx_dispatcher.h"
#include "pil.h"
#include "plx_serial.h"
#include "string.h"
#include "plx_sci.h"
#include "pin_map.h"
#include "gpio.h"
#include "xbar.h"
#include "asysctl.h"
#include "sysctl.h"
#include "plx_dio.h"
#include "plx_ain.h"
#include "plx_power.h"
#include "plx_pwm.h"
#include "math.h"
#include "epwm.h"
#include "hrpwm.h"


/* HAL Declarations */
void DevInit(uint32_t aDeviceClkConf);
void InitFlashHz(Uint32 clkHz);
void PieCntlInit(void);
void F28x_usDelay(long LoopCount);

// Clock configuration
#define PLX_DEVICE_SETCLOCK_CFG       (SYSCTL_OSCSRC_OSC2 | SYSCTL_IMULT(25) | \
                                       SYSCTL_REFDIV(1) | SYSCTL_ODIV(5) | \
                                       SYSCTL_SYSDIV(1) | SYSCTL_PLL_ENABLE | \
                                       SYSCTL_DCC_BASE_0)

#define SYSCLK_HZ 50000000L
#define LSPCLK_HZ (50000000L / 4l)

#define PLX_DELAY_US(A)  F28x_usDelay(((((long double) A * \
                                         1000.0L) / \
                                        (long double)20.000000L) - \
                                       9.0L) / 5.0L)
PIL_Obj_t PilObj;
PIL_Handle_t PilHandle = 0;
// external mode helper symbols
PIL_CONFIG_DEF(uint32_t, ExtMode_targetFloat_Size,
               sizeof(Controller_FloatType));
PIL_CONFIG_DEF(uint32_t, ExtMode_targetPointer_Size,
               sizeof(Controller_FloatType*));
PIL_CONFIG_DEF(uint32_t, ExtMode_sampleTime_Ptr,
               (uint32_t)&Controller_sampleTime);
PIL_CONFIG_DEF(uint32_t, ExtMode_checksum_Ptr,
               (uint32_t)&Controller_checksum);
      #if defined(Controller_NumTunableParameters) && \
   (Controller_NumTunableParameters > 0)
PIL_CONFIG_DEF(uint32_t, ExtMode_P_Ptr, (uint32_t)&Controller_P);
PIL_CONFIG_DEF(uint32_t, ExtMode_P_Size,
               (uint32_t)Controller_NumTunableParameters);
      #endif
      #if defined(Controller_NumExtModeSignals) && \
   (Controller_NumExtModeSignals > 0)
PIL_CONFIG_DEF(uint32_t, ExtMode_ExtModeSignals_Ptr,
               (uint32_t)&Controller_ExtModeSignals[0]);
PIL_CONFIG_DEF(uint32_t, ExtMode_ExtModeSignals_Size,
               (uint32_t)Controller_NumExtModeSignals);
      #endif
      #define CODE_GUID {0x09, 0x3c, 0x97, 0x5e, 0xdb, 0x2d, 0xb8, 0x40};

PIL_CONST_DEF(unsigned char, Guid[], CODE_GUID);
PIL_CONST_DEF(unsigned char, CompiledDate[], "11/11/2026 04:56 PM");
PIL_CONST_DEF(unsigned char, CompiledBy[], "PLECS Coder");
PIL_CONST_DEF(uint16_t, FrameworkVersion, PIL_FRAMEWORK_VERSION);
PIL_CONST_DEF(char, FirmwareDescription[], "TIC2000 Project (CPU0)");
PIL_CONST_DEF(uint16_t, StationAddress, 0);
PIL_CONST_DEF(uint32_t, BaudRate, 115200);
static void SerialPoll(PIL_Handle_t aHandle)
{
   PLXHAL_Serial_handleBreak(0);

   while(PLXHAL_Serial_rxIsReady(0))
   {
      // assuming that there will be a "break" when FIFO is empty
      PIL_SERIAL_IN(aHandle, (int16_t) PLXHAL_Serial_getChar(0));
   }
   int16_t ch;
   if(!PLXHAL_Serial_txIsBusy(0))
   {
      if(PIL_SERIAL_OUT(aHandle, &ch))
      {
         PLXHAL_Serial_putChar(0, ch);
      }
   }
}
#pragma DATA_SECTION(ScopeBuffer, "scope")
uint16_t ScopeBuffer[1040] /*__attribute__((aligned(16)))*/;
extern void PIL_setAndConfigScopeBuffer(PIL_Handle_t aPilHandle,
                                        uint16_t* aBufPtr, uint16_t aBufSize,
                                        uint16_t aMaxTraceWidthInWords);
extern const char * const Controller_checksum;
PLX_Serial_Obj_t SerialObjs[1];
PLX_Serial_Handle_t SerialHandles[1];
uint16_t PLXHAL_Serial_getChar(int16_t aChannel)
{
   return PLX_Serial_getChar(SerialHandles[aChannel]);
}

void PLXHAL_Serial_putChar(int16_t aChannel, uint16_t data)
{
   PLX_Serial_putChar(SerialHandles[aChannel], data);
}

void PLXHAL_Serial_putStr(int16_t aChannel, uint16_t *str)
{
   for (int i = 0; i < strlen((char *)str); i++)
   {
      PLXHAL_Serial_putChar(aChannel, str[i]);
   }
}

bool PLXHAL_Serial_rxIsReady(int16_t aChannel)
{
   return PLX_Serial_rxReady(SerialHandles[aChannel]);
}

bool PLXHAL_Serial_txIsBusy(int16_t aChannel)
{
   return PLX_Serial_txIsBusy(SerialHandles[aChannel]);
}

void PLXHAL_Serial_handleBreak(int16_t aChannel)
{
   if(PLX_Serial_breakOccurred(SerialHandles[aChannel]))
   {
      PLX_Serial_reset(SerialHandles[aChannel]);
   }
}
PLX_SCI_Obj_t SciObjs[1];
PLX_SCI_Handle_t SciHandles[1];
PLX_AIN_Handle_t AdcHandles[2];
PLX_AIN_Obj_t AdcObj[2];

float PLXHAL_ADC_getIn(uint16_t aHandle, uint16_t aChannel)
{
   return PLX_AIN_getInF(AdcHandles[aHandle], aChannel);
}
uint32_t PLXHAL_DISPR_getTimeStamp0()
{
   return DISPR_getTimeStamp0();
}

uint32_t PLXHAL_DISPR_getTimeStamp1()
{
   return DISPR_getTimeStamp1();
}

uint32_t PLXHAL_DISPR_getTimeStamp2()
{
   return DISPR_getTimeStamp2();
}

uint32_t PLXHAL_DISPR_getTimeStamp3()
{
   return DISPR_getTimeStamp3();
}

uint32_t PLXHAL_DISPR_getTimeStampB()
{
   return DISPR_getTimeStampB();
}

uint32_t PLXHAL_DISPR_getTimeStampD()
{
   return DISPR_getTimeStampD();
}

uint32_t PLXHAL_DISPR_getTimeStampP()
{
   return DISPR_getTimeStampP();
}

float PLXHAL_DISPR_getTask0LoadInPercent()
{
   return DISPR_getTask0LoadInPercent();
}
void PLXHAL_PWR_setEnableRequest(bool aEnable)
{
   PLX_PWR_setEnableRequest(aEnable);
   PLX_PWR_runFsm();
}

bool PLXHAL_PWR_isEnabled()
{
   return PLX_PWR_isEnabled();
}

void PLXHAL_PWR_syncdPwmEnable()
{
   PLX_PWR_syncdSwitchingEnable();
}
extern PLX_PWM_Handle_t EpwmHandles[];
// PWM Enable Functions
void PLXHAL_PWM_setToPassive(uint16_t aChannel)
{
   PLX_PWM_setOutToPassive(EpwmHandles[aChannel]);
}

void PLXHAL_PWM_setToOperational(uint16_t aChannel)
{
   PLX_PWM_setOutToOperational(EpwmHandles[aChannel]);
}

void PLXHAL_PWM_prepareSetOutToXTransition(uint16_t aHandle)
{
   PLX_PWM_prepareSetOutToXTransition(EpwmHandles[aHandle]);
}

// PWM Set Duty Cycle Function
        #pragma CODE_SECTION(PLXHAL_PWM_setDuty, "ramfuncs")
void PLXHAL_PWM_setDuty(uint16_t aHandle, float aDuty)
{
   PLX_PWM_setPwmDuty(EpwmHandles[aHandle], aDuty);
}

// PWM Set Dead Time Functions
        #pragma CODE_SECTION(PLXHAL_PWM_setRisingDelay, "ramfuncs")
void PLXHAL_PWM_setRisingDelay(uint16_t aChannel, float delay)
{
   PLX_PWM_setDeadTimeCountsRising(EpwmHandles[aChannel],
                                   delay * 5.000000e+07f);
}

        #pragma CODE_SECTION(PLXHAL_PWM_setFallingDelay, "ramfuncs")
void PLXHAL_PWM_setFallingDelay(uint16_t aChannel, float delay)
{
   PLX_PWM_setDeadTimeCountsFalling(EpwmHandles[aChannel],
                                    delay * 5.000000e+07f);
}

// PWM Set Sequence Functions
void PLXHAL_PWM_setSequence(uint16_t aChannel, uint16_t aSequence)
{
   PLX_PWM_setSequence(EpwmHandles[aChannel], aSequence);
}

void PLXHAL_PWM_setSequenceAq(uint16_t aChannel, uint32_t aSequenceAq)
{
   PLX_PWM_setSequenceAq(EpwmHandles[aChannel], aSequenceAq);
}

void PLXHAL_PWM_enableOutputSwap(uint16_t aChannel, bool aEnableSwap)
{
   PLX_PWM_enableOutputSwap(EpwmHandles[aChannel], aEnableSwap);
}
// Function for updating MEP using SFO
void PLXHAL_PWM_updateMEP()
{
   PLX_PWM_updateMEP();
}
    #pragma CODE_SECTION(PLXHAL_PWM_setDutyAB, "ramfuncs")
void PLXHAL_PWM_setDutyAB(uint16_t aHandle, float aDutyA, float aDutyB)
{
   PLX_PWM_setPwmDutyA(EpwmHandles[aHandle], aDutyA);
   PLX_PWM_setPwmDutyB(EpwmHandles[aHandle], aDutyB);
}

void PLXHAL_PWM_setOverflowSocDelay(uint16_t aHandle, float aPhase)
{
   PLX_PWM_setPwmDutyCGreaterThanZero(EpwmHandles[aHandle], 1.0f - aPhase);
}

void PLXHAL_PWM_setUnderflowSocDelay(uint16_t aHandle, float aPhase)
{
   PLX_PWM_setPwmDutyCSmallerThanFull(EpwmHandles[aHandle], aPhase);
}
PLX_PWM_Handle_t EpwmHandles[2];
PLX_PWM_Obj_t EpwmObj[2];
void PIL_setErrorMessage(PIL_Handle_t aPilHandle, const char* aMessage);
extern const char * Controller_errorStatus;
static void PanicCallback()
{
   PLX_PWR_emergencyOff();
}
extern PIL_Handle_t PilHandle;
DISPR_TaskObj_t TaskObj[1];
extern void Controller_step();
extern void Controller_enableTasksInterrupt();
extern void Controller_syncTimers();
static void Tasks(bool aInit, void * const aParam)
{
   if(Controller_errorStatus)
   {
      PIL_setErrorMessage(PilHandle, Controller_errorStatus);
      return;
   }
   if(aInit)
   {
      Controller_enableTasksInterrupt();
   }
   else
   {
      Controller_step();
   }
}
interrupt void Controller_baseTaskInterrupt(void)
{
   AdcbRegs.ADCINTFLGCLR.bit.ADCINT1 = 1;            // clear ADCINT1 flag reinitialize for next SOC
   PieCtrlRegs.PIEACK.all = PIEACK_GROUP1;  // acknowledge interrupt to PIE (All ADCS in group 1)
   IER |= M_INT1;

   DISPR_dispatch();
}
          #pragma \
   CODE_SECTION(Controller_hasBaseTaskOverrunOccurred, "ramfuncs")
static inline bool Controller_hasBaseTaskOverrunOccurred()
{
   return AdcbRegs.ADCINTFLG.bit.ADCINT1;
}


/* Interrupt Enable Code */
void Controller_enableTasksInterrupt(void)
{
   IER |= M_INT1;

}

/* Timer Synchronization Code */
void Controller_syncTimers(void)
{
   CpuSysRegs.PCLKCR0.bit.TBCLKSYNC = 1;        // start all the timers synced

}

/* Background task */
void Controller_background(void)
{

}

/* HAL Initialization Code */
static bool HalInitialized = false;
void Controller_initHal()
{

   if(HalInitialized == true)
   {
      return;
   }
   HalInitialized = true;

   // Pre init code
   SysCtl_disableWatchdog();
   {
      uint32_t sysPllConfig = PLX_DEVICE_SETCLOCK_CFG;
      DevInit(sysPllConfig);

      SysCtl_setLowSpeedClock(SYSCTL_LSPCLK_PRESCALE_4);
   }

   InitFlashHz(SYSCLK_HZ);

   // set cpu timers to same clock as ePWM
   CpuTimer0Regs.TPR.all = 0;
   CpuTimer1Regs.TPR.all = 0;
   CpuTimer2Regs.TPR.all = 0;
   EALLOW;
   CpuSysRegs.PCLKCR0.bit.CPUTIMER0 = 1;
   CpuSysRegs.PCLKCR0.bit.CPUTIMER1 = 1;
   CpuSysRegs.PCLKCR0.bit.CPUTIMER2 = 1;
   CpuSysRegs.PCLKCR0.bit.TBCLKSYNC = 0;  // stop all the TB clocks
   EDIS;
   PilHandle = PIL_init(&PilObj, sizeof(PilObj));
   PIL_setGuid(PilHandle, PIL_GUID_PTR);
   PIL_setChecksum(PilHandle, Controller_checksum);
   PIL_setAndConfigScopeBuffer(PilHandle, (uint16_t *)&ScopeBuffer, 1040, 20);
   PIL_setNodeAddress(PilHandle, PIL_D_StationAddress);
   PIL_setSerialComCallback(PilHandle, (PIL_CommCallbackPtr_t)SerialPoll);
   {
      for(int i = 0; i < 1; i++)
      {
         SerialHandles[i] =
            PLX_Serial_init(&SerialObjs[i], sizeof(SerialObjs[i]));
      }
   }
   {
      for(int i = 0; i < 1; i++)
      {
         SciHandles[i] =
            PLX_SCI_init(&SciObjs[i], sizeof(SciObjs[i]));
      }
   }
   {
      // early system configuration
      PLX_DIO_sinit();
      GPIO_setAnalogMode(21, GPIO_ANALOG_DISABLED);
      GPIO_setAnalogMode(28, GPIO_ANALOG_DISABLED);
   }
   // setup analog voltage references
   {
      SetVREF(ADC_ADCA, ADC_INTERNAL, ADC_VREF3P3);
   }
   {
      PLX_AIN_sinit(50000000);

      for (int i = 0; i < 2; i++)
      {
         AdcHandles[i] = PLX_AIN_init(&AdcObj[i], sizeof(AdcObj[i]));
      }
   }
   // configure ADC A
   {
      PLX_AIN_AdcParams_t params;
      PLX_AIN_setDefaultAdcParams(&params, 3.300000, 0);
      PLX_AIN_configure(AdcHandles[0], (PLX_AIN_Unit_t)0, &params);
   }
   // configure SOC0 of ADC-A to measure ADCIN6
   {
      PLX_AIN_ChannelParams_t params;
      PLX_AIN_setDefaultChannelParams(&params);
      params.scale =  1.000000000e+00f;
      params.offset = 0.000000000e+00f;
      // set SOC trigger to PWM1
      params.ADCSOCxCTL.bit.TRIGSEL = 5;
      params.ADCSOCxCTL.bit.ACQPS = 3;
      PLX_AIN_setupChannel(AdcHandles[0], 0, 6, &params);
   }
   // configure SOC1 of ADC-A to measure ADCIN10
   {
      PLX_AIN_ChannelParams_t params;
      PLX_AIN_setDefaultChannelParams(&params);
      params.scale =  1.000000000e+00f;
      params.offset = 0.000000000e+00f;
      // set SOC trigger to PWM1
      params.ADCSOCxCTL.bit.TRIGSEL = 5;
      params.ADCSOCxCTL.bit.ACQPS = 3;
      PLX_AIN_setupChannel(AdcHandles[0], 1, 10, &params);
   }
   // configure ADC B
   {
      PLX_AIN_AdcParams_t params;
      PLX_AIN_setDefaultAdcParams(&params, 3.300000, 0);
      PLX_AIN_configure(AdcHandles[1], (PLX_AIN_Unit_t)1, &params);
   }
   // configure SOC0 of ADC-B to measure ADCIN2
   {
      PLX_AIN_ChannelParams_t params;
      PLX_AIN_setDefaultChannelParams(&params);
      params.scale =  1.000000000e+00f;
      params.offset = 0.000000000e+00f;
      // set SOC trigger to PWM1
      params.ADCSOCxCTL.bit.TRIGSEL = 5;
      params.ADCSOCxCTL.bit.ACQPS = 3;
      PLX_AIN_setupChannel(AdcHandles[1], 0, 2, &params);
   }
   // configure SOC1 of ADC-B to measure ADCIN0
   {
      PLX_AIN_ChannelParams_t params;
      PLX_AIN_setDefaultChannelParams(&params);
      params.scale =  1.000000000e+00f;
      params.offset = 0.000000000e+00f;
      // set SOC trigger to PWM1
      params.ADCSOCxCTL.bit.TRIGSEL = 5;
      params.ADCSOCxCTL.bit.ACQPS = 3;
      PLX_AIN_setupChannel(AdcHandles[1], 1, 0, &params);
   }
   {
      PLX_PWR_sinit();
      PLX_DIO_sinit();
      static PLX_DIO_Obj_t doutObj;
      PLX_DIO_Handle_t doutHandle = PLX_DIO_init(&doutObj, sizeof(doutObj));
      PLX_DIO_OutputProperties_t props = {
         0
      };
      props.enableInvert = true;
      PLX_DIO_configureOut(doutHandle, 21, &props);
      PLX_PWR_configure(doutHandle, 9960);
   }
   PLX_PWM_sinit();
   for (int i = 0; i < 2; i++)
   {
      EpwmHandles[i] = PLX_PWM_init(&EpwmObj[i], sizeof(EpwmObj[i]));
   }
   // configure PWM1 at 9960.2 Hz in triangle mode
   // soc='z'
   {
      PLX_PWM_Params_t params;
      PLX_PWM_setDefaultParams(&params);
      params.outMode = PLX_PWM_OUTPUT_MODE_DUAL;
      params.reg.TBPRD = 2510;
      params.reg.TBCTL.bit.CTRMODE = 2;
      params.reg.CMPCTL.bit.LOADAMODE = CC_CTR_ZERO_PRD;
      // active state is high
      params.reg.DBCTL.bit.POLSEL = 2; // DB_ACTV_HIC
      // enable deadtime insertion
      params.reg.DBCTL.bit.OUT_MODE = 3; // DB_FULL_ENABLE
      params.reg.DBCTL.bit.IN_MODE = 0; // DBA_ALL
      // TZ settings
      params.reg.TZSEL.bit.CBC1 = 0;
      params.reg.TZSEL.bit.OSHT1 = 0;
      params.reg.TZSEL.bit.CBC2 = 0;
      params.reg.TZSEL.bit.OSHT2 = 0;
      params.reg.TZSEL.bit.CBC3 = 0;
      params.reg.TZSEL.bit.OSHT3 = 0;
      // force low when tripped
      params.reg.TZCTL.bit.TZA = 2;
      params.reg.TZCTL.bit.TZB = 2;
      PLX_PWM_configure(EpwmHandles[0], 1, &params);
      // configure deadtime to 2.000000e-06/2.000000e-06 seconds (rising/falling)
      PLX_PWM_setDeadTimeCounts(EpwmHandles[0], 100.000000, 100.000000);
      // PWM sequence starting with active state
      PLX_PWM_setSequence(EpwmHandles[0], 1);
      EPwm1Regs.ETSEL.bit.SOCASEL = 1;
      EPwm1Regs.ETPS.bit.SOCPSSEL = 1;
      EPwm1Regs.ETSOCPS.bit.SOCAPRD2 = 1;
      EPwm1Regs.ETSEL.bit.SOCAEN = 1;
   }
   // configure PWM2 at 9960.2 Hz in triangle mode
   //
   {
      PLX_PWM_Params_t params;
      PLX_PWM_setDefaultParams(&params);
      params.outMode = PLX_PWM_OUTPUT_MODE_DUAL;
      params.reg.TBPRD = 2510;
      params.reg.TBCTL.bit.CTRMODE = 2;
      params.reg.CMPCTL.bit.LOADAMODE = CC_CTR_ZERO_PRD;
      // active state is high
      params.reg.DBCTL.bit.POLSEL = 2; // DB_ACTV_HIC
      // enable deadtime insertion
      params.reg.DBCTL.bit.OUT_MODE = 3; // DB_FULL_ENABLE
      params.reg.DBCTL.bit.IN_MODE = 0; // DBA_ALL
      // TZ settings
      params.reg.TZSEL.bit.CBC1 = 0;
      params.reg.TZSEL.bit.OSHT1 = 0;
      params.reg.TZSEL.bit.CBC2 = 0;
      params.reg.TZSEL.bit.OSHT2 = 0;
      params.reg.TZSEL.bit.CBC3 = 0;
      params.reg.TZSEL.bit.OSHT3 = 0;
      // force low when tripped
      params.reg.TZCTL.bit.TZA = 2;
      params.reg.TZCTL.bit.TZB = 2;
      PLX_PWM_configure(EpwmHandles[1], 2, &params);
      // configure deadtime to 2.000000e-06/2.000000e-06 seconds (rising/falling)
      PLX_PWM_setDeadTimeCounts(EpwmHandles[1], 100.000000, 100.000000);
      // PWM sequence starting with active state
      PLX_PWM_setSequence(EpwmHandles[1], 1);

   }
   DISPR_sinit();
   DISPR_configure((uint32_t)(5020), PilHandle, &TaskObj[0],
                   sizeof(TaskObj)/sizeof(DISPR_TaskObj_t));
   DISPR_registerIdleTask(&Controller_background);
   DISPR_registerHasBaseTaskOverrunOccurredCallback(
                                                    &Controller_hasBaseTaskOverrunOccurred);
   DISPR_registerSyncCallback(&Controller_syncTimers);
   DISPR_setPowerupDelay(10);
   DISPR_registerPanicCallback(&PanicCallback);
   {
      static int taskId = 0;
      // Task 0 at 9.960159e+03 Hz
      DISPR_registerTask(0, &Tasks, 5020L, (void *)&taskId);
   }
   EALLOW;
   AdcbRegs.ADCINTSEL1N2.bit.INT1CONT = 0;  // disable ADCINT1 Continuous mode
   AdcbRegs.ADCINTSEL1N2.bit.INT1SEL = 1;  // setup EOC1 or OSINT(1 - 15) to trigger ADCINT1
   AdcbRegs.ADCINTSEL1N2.bit.INT1E = 1;  // enable ADCINT1
   AdcbRegs.ADCCTL1.bit.INTPULSEPOS = 1;  // ADCINT1 trips after AdcResults latch
   EDIS;
   EALLOW;
   *(PINT *)((uint32_t)(&PieVectTable.ADCA1_INT) + ((uint32_t)1)*
             sizeof(PINT *)) = &Controller_baseTaskInterrupt;
   PieCtrlRegs.PIEIER1.all |= 2;
   PieCtrlRegs.PIEACK.all = PIEACK_GROUP1;
   EDIS;


   // Post init code (for modules that depend on other modules)
   PLX_SCI_setInterface(SerialHandles[0], SciHandles[0]);
   {
      PLX_SCI_Unit_t unit = PLX_SCI_SCI_A;
      PLX_Serial_config(SerialHandles[0], &unit, 12500000);
   }
   PLX_Serial_setupPort(SerialHandles[0], 115200);
   {
      // late system configuration
      GPIO_setAnalogMode(228, GPIO_ANALOG_ENABLED);
      GPIO_setAnalogMode(230, GPIO_ANALOG_ENABLED);
      GPIO_setAnalogMode(226, GPIO_ANALOG_ENABLED);
      GPIO_setAnalogMode(253, GPIO_ANALOG_ENABLED);
      GPIO_setPinConfig(GPIO_0_EPWM1_A);
      GPIO_setPinConfig(GPIO_1_EPWM1_B);
      GPIO_setPinConfig(GPIO_2_EPWM2_A);
      GPIO_setPinConfig(GPIO_3_EPWM2_B);
      GPIO_setPadConfig(21, GPIO_PIN_TYPE_STD);
      GPIO_setDirectionMode(21, GPIO_DIR_MODE_OUT);
      GPIO_setPinConfig(GPIO_28_SCIA_RX);
      GPIO_setPinConfig(GPIO_29_SCIA_TX);
   }
   PLX_PWR_registerPwmChannel(EpwmHandles[0]);
   PLX_PWR_registerPwmChannel(EpwmHandles[1]);


   // If applicable, boot secondary core(s)

}
