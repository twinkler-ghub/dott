# DOTT - Debugger-Based On-Target Testing

This file provides a short overview about the scope of the Debugger-Based On Target Testing (DOTT)
framework followed by a quick step-by-step guide to get people started. Full documentation is provided
online at the [GitHub DOTT documentation site][6].

DOTT is a framework for on-target testing of firmware for __Arm Cortex-M__ microcontrollers.
Tests are implemented in Python and they are executed on a host PC. The host PC is connected
to the target (microcontroller) via a debugger, typically using SWD or JTAG. At this time, DOTT
relies on [Segger J-Link][1] debug probes.
```
|-----------|                                            |------------|
|  HOST PC  |   USB                          SWD         |   TARGET   |
|           | <----> J-Link Debugger <-----------------> |            |
|   Tests   |                                            | Unmodified |
| in Python | <----> Other Test Equipment <------------> |  Firmware  |
|           |   USB   (e.g., RasperryPi)   I2C, SPI, ... |            |
|-----------|                                            |------------|
```

## Where it's from & What it does

DOTT was internally developed at [ams AG](http://www.ams.com) to simplify automated testing of firmware for
Arm Cortex-M microcontrollers. In spring 2021 it was decided to release DOTT via GitHub to the general public.
DOTT continues to be used and maintained by ams AG. Contributions from industry and the open-source
community are highly encouraged.

DOTT aims to enable firmware testing ...
* ... __without modifications__ of the firmware for the sake of testing
* ... __without mocking__ of, e.g., peripherals
* ... __with support for selective injection__ of data into the execution
* ... on the __original target device__
* ... using the __original compiler__

DOTT also comes with the benefit that the test runner and tests are executed on the host PC and do not have to
be compiled for the target device or downloaded to it. Executing the tests on a host PC also makes it easy to
integrate whatever __additional test equipment__ is available/required (e.g., stimulus generation, interface
hardware, logic analyzers, ...).

## How it works

DOTT relies on the GNU Debugger (GDB) and its machine interface (MI). DOTT allows you to do a multitude of
things such as writing very basic unit tests where you are calling functions implemented in your firmware
with parameters of your choice. Suppose your firmware contains a function `example_Addition`. You can call it from
a test in Python as follows:
```python
def test_example_Addition(self, target_load, target_reset):
    res = dott().target.eval('example_Addition(31, 11)')
    assert(42 == res)
```
You did not only test that your function returns 42 when feeding in 31 and 11 as parameters but along the way,
via the `target_load` and `target_reset` pytest fixtures coming with DOTT, you also loaded the firmware binary
to the target device and performed a target reset. This ensures that the target is in a known state when you
execute your test.

A slightly more involved example is the following one. Suppose your firmware has a function called
`test_example_AdditionSubcalls` which in turn calls two other functions, namely `example_GetA` which returns
the value of a local variable `a` and `exammple_GetB` which modifies the value of pointer variable `b`. The
following test first calls `example_AdditionSubcalls` and checks for the expected result. Next, it changes
what `example_GetA` and `example_GetB` return and then again checks if the new result matches the expected one.
This demonstrates how DOTT can be used to inject data into the program execution which is very useful to test
corner cases.
```python
def test_example_Simple(self, target_load, target_reset):
    res = dott().target.eval('example_AdditionSubcalls()')
    assert (63 == res)

    # Now tweak the sub function return values and see if example_AdditionSubcalls delivers the new expected result
    class IpA(InterceptPoint):
        def reached(self):
            self.ret(10)

    class IpB(InterceptPoint):
        def reached(self):
            self.eval('*b = 89')
            self.ret(0)

    ipa = IpA('example_GetA')
    ipb = IpB('example_GetB')

    res = dott().target.eval('example_AdditionSubcalls()')

    ipa.delete()
    ipb.delete()

    assert(99 == res)
```
These examples are barely scratching the surface of how you can use DOTT for firmware testing and things really
start to get fun when you advance from basic unit/component testing to system testing where you integrate additional
test equipment. With DOTT you can then observe, e.g., which (side)effects external test stimuli have on your firmware.
System testing examples can be found in the [System Testing Section][9] of the DOTT documentation.

## Dependencies and Requirements

__Required__
* host OS (tested): Windows 10 (64bit), Ubuntu Linux 20.04 (64bit)
* Python 3.7 or newer (e.g., [WinPython][2])
* [Segger J-Link][1] debug probe or STM32 eval board with ST-Link converted to J-Link
* Segger [J-Link Software Pack][3]. __Notice:__ The following version should be avoided since they have known issues
related to SRAM download: v6.50, v6.52(a-c)

__Recommended__
* [STM32F072 Nucleo-64][5] board which is used as reference platform for the examples coming with DOTT

__Optional__
* Arm Compiler 6 to re-build the example firmware images (*)
* GNU Make + Busybox as build environment to re-build the example firmware images
* RaspberryPi as test equipment to, e.g., provide stimuli via I2C or SPI to the system under test

(*) GCC support is planned for a future release.

## Setup Instructions
* As a pre-requisite download and install the [Segger J-Link software][3] to its default location.

* If you are using the recommended STM32F072 Nucleo-64 reference board, convert its ST-LINK debugger to a J-Link
debugger by the instructions from the [DOTT documentation (reference board section)][11].

* It is assumed that you have a Python interpreter installed. A recommended, self-contained Python
distribution for Windows is [WinPython][2]. For detailed setup instructions and Linux-specific aspects please check the [DOTT Setup Guide][7].

* It is recommended (but not required) to create and activate a virtual environment for DOTT:
```shell script
$ python -m venv dott_venv
$ dott_venv\Scripts\activate.bat
```

* DOTT can be installed using pip from the Python package index (PyPi) using pip:
```shell script
$ pip install ams-dott
```

* This installs all the required dependencies including the *ams-dott-runtime* package. The *ams-dott-runtime*
contains binary dependencies required by DOTT. These are the GNU debug (GDB) client for Arm Cortex-M
processors as distributed by Arm in the [GNU Arm Embedded Toolchain][4]. Since the Arm's GNU Arm Embedded Toolchain
does not yet come with Python 3.x support for GDB-internal scripting also the required Python 2.7 dependencies are
included in the ams-dott-runtime (Windows only). Note that only a minor fraction of DOTT uses the 2.7 environment
while the majority (including all tests you write) reside in the 3.x environment and interfaces GDB via its machine
interface (MI). The 2.7 dependency will vanish as soon as Arm moves the GNU Arm Embedded Toolchain to Python 3.x.

* Download the zip archive providing documentation and example projects from the [DOTT Github releases website][10] and
unpack it to your disk.

* Make sure that the STM32F072 Nucleo-64 board is connected to your PC and that its ST-LINK is already converted
to J-Link. Open a shell (and activate the DOTT virtual environment if you are using venv). Next, execute the
example tests from the zip file:
```shell script
$ cd examples\01_component_testing\host
$ pytest
```

* This should generate an output similar to the one below. This indicates that you have correctly
installed DOTT and successfully executed your first tests. Please consult the DOTT documentation to learn
more about basic [component testing][8] as in this example as well as about more advanced [system testing][9]
concepts.
```shell script
[INFO] dott.py @197: DOTT runtime:          c:\tmp\venv_dott_install_test/dott_data (package-internal)
[INFO] dott.py @198: DOTT runtime version:  package-internal
[INFO] dott.py @201: work directory:        C:\tmp\dott_doc_examples_20191217\examples
[INFO] dott.py @246: BL ELF (load):         None
[INFO] dott.py @254: BL ELF (symbol):       None
[INFO] dott.py @262: BL ADDR (symbol):      0x0
[INFO] dott.py @268: APP ELF (load):        01_component_testing/target/build/dott_example_01/dott_example_01.bin.elf
[INFO] dott.py @275: APP ELF (symbol):      01_component_testing/target/build/dott_example_01/dott_example_01.axf
[INFO] dott.py @279: Device name:           STM32F072RB
[INFO] dott.py @286: Device endianess:      little
[INFO] dott.py @290: J-LINK interface:      SWD
[INFO] dott.py @294: J-LINK speed (set):    15000
[INFO] dott.py @306: GDB client binary:     c:\tmp\venv_dott_install_test/dott_data/apps/gdb/bin/arm-none-eabi-gdb-py
[INFO] dott.py @314: GDB server address:    10.10.171.84
[INFO] dott.py @320: GDB server port:       2331
[INFO] dott.py @344: GDB server assumed to be already running (not started by DOTT).
[INFO] dott.py @390: Std. target mem model for DOTT default fixtures:  TargetMemModel.TESTHOOK
[INFO] fixtures.py @46: Triggering download of APP to FLASH...
PASSED                                                                                                                                                   [  4%]
test_example_functions.py::TestExampleFunctions::test_example_NoArgsStatic PASSED                                                                        [  9%]
test_example_functions.py::TestExampleFunctions::test_example_Addition PASSED                                                                            [ 14%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionPtr PASSED                                                                         [ 19%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionPtr_Alternate PASSED                                                               [ 23%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionPtr_AlternateArray PASSED                                                          [ 28%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionPtrRet PASSED                                                                      [ 33%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionPtrRet_Alternate PASSED                                                            [ 38%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionStruct PASSED                                                                      [ 42%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionStruct_Alternate PASSED                                                            [ 47%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionStruct_ctypes PASSED                                                               [ 52%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionStructPtr PASSED                                                                   [ 57%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionStructPtr_Alternate PASSED                                                         [ 61%]
test_example_functions.py::TestExampleFunctions::test_example_ManyArgs PASSED                                                                            [ 66%]
test_example_functions.py::TestExampleFunctions::test_example_CustomOperation PASSED                                                                     [ 71%]
test_example_functions.py::TestExampleFunctions::test_example_ArgString PASSED                                                                           [ 76%]
test_example_functions.py::TestExampleFunctions::test_example_SumElements PASSED                                                                         [ 80%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionSubcalls PASSED                                                                    [ 85%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionSubcallsBasicIntercept PASSED                                                      [ 90%]
test_example_functions.py::TestExampleFunctions::test_example_AdditionSubcallsExtIntercept PASSED                                                        [ 95%]
test_example_functions.py::TestExampleFunctions::test_global_data_access PASSED                                                                          [100%]

-------------------- generated xml file: C:\tmp\dott_doc_examples_20191217\examples\test_results.xml ---------------------
===================================================================== 21 passed in 10.41s =====================================================================
```

## Contributors

* Thomas Winkler <thomas.winkler@ams.com>, ams AG, [http://www.ams.com](http://www.ams.com)

[1]: https://www.segger.com/products/debug-probes/j-link/
[2]: http://winpython.sourceforge.net/
[3]: https://www.segger.com/downloads/jlink/#J-LinkSoftwareAndDocumentationPack
[4]: https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm
[5]: https://www.st.com/en/evaluation-tools/nucleo-f072rb.html
[6]: https://twinkler-ams-osram.github.io/dott_docu/
[7]: https://twinkler-ams-osram.github.io/dott_docu//SetupAndTarget.html
[8]: https://twinkler-ams-osram.github.io/dott_docu//ComponentTesting.html
[9]: https://twinkler-ams-osram.github.io/dott_docu//SystemTesting.html
[10]: https://github.com/twinkler-ams-osram/dott/releases
[11]: https://twinkler-ams-osram.github.io/dott_docu//ReferencePlatform.html
