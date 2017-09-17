# C++/Fortran Mixed Programming with VS2010 and IVF2013
SWAT是我们学习水文模型的很好范例，它的源码由Fortran编写，且在持续更新中，最新版本为2014年9月30日更新的[SWAT2012 rev.629](http://swat.tamu.edu/software/swat-executables/)。为了更好地研究、利用这个宝库，我们需要一些Fortran基本知识，保证能看懂源码，并学会如何实现C++调用Fortran动态链接库（DLL），达到为我所用的目的。
## 目录
- 1、[Fortran基本语法](#1--fortran基本语法)
- 2、[在VS2010和IVF2013环境下实现混合编程](#2--在vs2010和ivf2013环境下实现混合编程)
- 3、[c中实现fortran接口](#3--c中实现fortran接口)

>主要参考资料

>1、http://www.neurophys.wisc.edu/comp/docs/notes/not017.html
>2、http://micro.ustc.edu.cn/Fortran/
>3、http://arnholm.org/software/cppf77/cppf77.htm
（The main idea of interfacing C++ and FORTRAN presented in this document is based on the SUBROUTINE and FUNCTION language elements of F77. Other language elements, like common blocks, are not viewed as suitable for interfacing directly within C++.）
>4、https://sukhbinder.wordpress.com/2011/04/14/how-to-create-fortran-dll-in-visual-studio-with-intel-fortran-compiler/
>5、http://www.duote.com/tech/6/15005.html

## 1  Fortran基本语法
Fortran基本数据类型有：
* INTEGER，对应int
* REAL，对应float
* DOUBLE PRECISION，对应double
* COMPLEX,复数，可看成包含2个REAL的结构体，第一个为实数，第二个为虚数，因此可用C++中的struct或class表示
* LOGICAL，对应
* CHARACTER [*n], n is the optional string length, range from 1 to 32767

数组：
* Fortran最高支持7维数组，数据始终保存在一段连续的内存中，并有标准的组织顺序。一维数组的存储和C++是一致的，因此对一维数组，可以直接相互传递。二维或更高维数组Fortran采用的“列优先”存储方式，这和C++“行优先”方式相反。

[返回目录](#目录)

## 2  在VS2010和IVF2013环境下实现混合编程
编程环境：C++使用Visual Studio 2010，Fortran使用Intel Visual Fortran Composer XE 2013 SP1. （IVF2011以上版本均可）
### 2.1 先来一个例子
1、首先打开VS2010，文件-新建项目，选择Intel Visual Fortran下的Library，选择Dynamic-link Library
![cppfortran example](https://github.com/qualitydog/pic/blob/master/pic/fig1.png)
2、右键FirstFortranDLL，添加-新建项，新建FirstFortranDLL.f，输入以下代码:

```
SUBROUTINE TEST1(a,b)
       !! 没有返回值的子例程
       !! !DIR$语句中加入了C调用约定，且参数传递方式变为传值方式
       !! 相应的C++代码中需添加：
       !! extern "C"{void _cdecl test1(int x,int y);}
 !DIR$ ATTRIBUTES C,DLLEXPORT :: TEST1
           INTEGER a,b
           a = a + 1
           b = b + 2
           RETURN
       END SUBROUTINE TEST1
       
       SUBROUTINE test2(a,b)
       !! 没有返回值的子例程
       !! 此时，Fortran缺省的参数传递方式是引用方式
       !! 在C/C++函数原型的声明中使用_stdcall关键字来指明过程采用STDCALL调用约定
       !! extern "C"{_stdcall test2(int* x,int* y);}
 !DIR$ ATTRIBUTES DLLEXPORT :: test2
           INTEGER a,b
           a = a + 1
           b = b + 2
           RETURN
       END SUBROUTINE test2
       
       FUNCTION ADD(a,b)
       !! 有返回值的子函数
       IMPLICIT NONE
 !DIR$ ATTRIBUTES C,DLLEXPORT :: ADD
           INTEGER a,b,add
           add = a + b
           RETURN
       END
       
       FUNCTION multiply(a,b)
       !! 有返回值的子函数
       IMPLICIT NONE
 !DIR$ ATTRIBUTES C,DLLEXPORT :: multiply
           INTEGER a,b,multiply
           !a = 0
           !b = 0
           !multiply = 0
           multiply = a * b
           WRITE(*,*) "a * b = ",multiply
           RETURN
       END
       
       FUNCTION multiply2(a,b)
       !! 有返回值的子函数
       IMPLICIT NONE
 !DIR$ ATTRIBUTES DLLEXPORT :: multiply2
           INTEGER a,b,multiply2
           !a = 0
           !b = 0
           !multiply = 0
           multiply2 = a * b
           WRITE(*,*) "a * b = ",multiply2
           RETURN
       END
       
       FUNCTION divided(a,b)
       !! 有返回值的子函数
       IMPLICIT NONE
 !DIR$ ATTRIBUTES C, DLLEXPORT :: divided
           REAL a,b,divided
           divided = a / b
           WRITE(*,*) "a / b = ",divided
           RETURN
       END
```
3、右键FirstFortranDLL，生成（Build），不出意外的话，在Debug文件夹下就会发现如下三个文件（只复制DLL和LIB也可），复制到C++工程的Debug，并通过右键-添加现有项将LIB添加至工程：

![](https://github.com/qualitydog/pic/blob/master/pic/fig2.png)

用Dependency Walker打开DLL，可以看到我们定义的函数名等信息，发现均为小写：

![](https://github.com/qualitydog/pic/blob/master/pic/fig3.png)

OK，以上3 步便是将Fortran源码编译成了可供C++调用的库，接下来要新建一个C++控制台项目，空项目即可：
4、新建C++文件，输入以下代码：
```
 #include <cstdio>
 #include <iostream>
 #include <Windows.h>
 using namespace std;
 extern "C"{void _cdecl test1(int ,int );}
 extern "C"{void _stdcall test2(int* ,int* );}
 extern "C"{int _cdecl add(int ,int );}
 extern "C"{int _cdecl multiply(int ,int );}
 extern "C"{int _stdcall multiply2(int* ,int* );}
 extern "C"{float _cdecl divided(float ,float );}
 int main(int argc, char* argv[])
 {
 	int a=41,b=5,sum=0,mul=0,mul2=0;
 	float c=10.2f,d=4.0f,divi=0.0f;
 	test1(a,b);
 	sum=add(a,b);
 	cout<<"a="<<a<<endl;
 	cout<<"b="<<b<<endl;
 	cout<<"sum="<<sum<<endl;
 	test2(&a,&b);
 	sum=add(a,b);
 	mul=multiply(a,b);
 	mul2=multiply2(&a,&b);
 	divi=divided(c,d);
 	cout<<"a="<<a<<endl;
 	cout<<"b="<<b<<endl;
 	cout<<"sum="<<sum<<endl;
 	cout<<"mul="<<mul<<endl;
 	cout<<"mul2="<<mul2<<endl;
 	cout<<"divi="<<divi<<endl;
 	system("pause");
 	return 0;
 }
```
5、这时候点编译运行会出现一系列的错误，比如：
error LNK1104: 无法打开文件“ifconsol.lib”

![](https://github.com/qualitydog/pic/blob/master/pic/fig4.png)
![](https://github.com/qualitydog/pic/blob/master/pic/fig5.png)

这些错误的出现一般是没有正确引用库造成的，因此，在项目属性下找到VC++目录，点开库目录，添加以下东西：
software.intel.com/en-us/articles/configuring-visual-studio-for-mixed-language-applications/

![](https://github.com/qualitydog/pic/blob/master/pic/fig6.png)

此外，还有一种错误是因为编译器找不到这个函数名，为什么找不到，这里需要补一下C/C++/Fortran的命名规范还有Name Mangling了，这篇博文写的很好(http://blog.csdn.net/hanyujianke/article/details/8622041)。
比如我现在的错误是：

![](https://github.com/qualitydog/pic/blob/master/pic/fig7.png)

而在Dependency Walker中查看DLL：

![](https://github.com/qualitydog/pic/blob/master/pic/fig8.png)

利用VS命令提示（2010），cd到LIB文件夹下，用dumpbin –exports *.lib命令查看：

![](https://github.com/qualitydog/pic/blob/master/pic/fig9.jpg)

发现DLL和LIB中均是“_sub1ar@4”而C++调用的时候提示无法解析“_sub1ar@8”，看来还是Fortran预编译语句出了问题！
在IVF帮助文档里搜索 ATTRIBUTES C and STDCALL，可以发现一些有用的信息，比如

+ 如果在子程序中指定C或STDCALL，参数（除了数组和字符串）是值传递；
+ 在32位架构的机器上，会在函数名前加上下划线_，如果指定了STDCALL，还会在函数名后加上@+数字，如_sub1@12；
+ 字符串传递规则：
    + 默认地，在参数列表最后隐含长度信息
    + 如果只指定C或STDCALL，所有系统下，传递字符串的第一个字符，且填充0至INTEGER（4）长度
    + 如果指定C或STDCALL，且为参数指定了REFERENCE，在所有系统下，字符串不传递长度
    + 如果指定C或STDCALL，且为整个程序指定了REFERENCE（不为参数指定REFERENCE），则所有系统下，字符串带长度传递

因此，综合了帮助文档和博客信息，我们将之前的Fortran函数预编译语句：
!DIR$ ATTRIBUTES DLLEXPORT :: SUBONE 或 !DIR$ ATTRIBUTES C,DLLEXPORT :: SUBONE
修改为：
!DIR$ ATTRIBUTES STDCALL,REFERENCE,DLLEXPORT :: SUBONE
便可成功运行！切记！
6、编译运行，可得结果：

![](https://github.com/qualitydog/pic/blob/master/pic/fig10.png)

由结果我们可以看到，当参数传递是值传递时，结果是正确的，而引用传递则出现错误。原因在于Fortran代码中需要加上一句：
!DIR$ ATTRIBUTES REFERENCE :: VARIABLES  !让编译器知道，此参数为引用传递，加上之后即为正确结果

```
extern "C"{int _cdecl multiply(int ,int );}  //值传递
extern "C"{int _stdcall multiply2(int& ,int& );}//引用传递
```

### 2.2 一些错误的解决方案
我们在实现C/C++调用Fortran功能时经常会遇到的一些问题和解决方法，http://blog.csdn.net/hjh2005/article/details/7487546 这篇博客给出了较好的解决方案

#### 2.2.1 在编译调用的C/C++程序时出现了一大堆的连接错误信息

~~~
1>LIBCMTD.lib(dbgheap.obj) : error LNK2005: __CrtSetCheckCount already defined in MSVCRTD.lib(MSVCR90D.dll)
1>LIBCMTD.lib(dbghook.obj) : error LNK2005: __crt_debugger_hook already defined in MSVCRTD.lib(MSVCR90D.dll)
1>LIBCMTD.lib(setlocal.obj) : error LNK2005: __configthreadlocale already defined in MSVCRTD.lib(MSVCR90D.dll)
1>LIBCMTD.lib(tidtable.obj) : error LNK2005: __encode_pointer already defined in MSVCRTD.lib(MSVCR90D.dll)
1>LIBCMTD.lib(tidtable.obj) : error LNK2005: __decode_pointer already defined in MSVCRTD.lib(MSVCR90D.dll)
~~~

以上错误都是函数重定义的错误，这是由于调用程序的“运行时库”类型和被调用程序的“运行时库”类型不一致造成的。解决方案是：
先看被调用的Fortran动态或静态库程序的形式库的类型，在“项目->属性->Fortran->Libraris-> Runtime Library"，再看调用的C/C++程序的形式库的类型，在”项目->属性->Configuration Properties->C/C++->Code Generation->Runtime Library“;

|        | Fortran (Runtime Library)   |  C/C++ (Runtime Library)  |
| ------------------- | -----  | :----:  |
| 静态库（Lib）、Debug  | Debug Multithreaded (/libs:static /threads /dbglibs) |   Multi-threaded Debug (/MTd)    |
| 静态库、Release       |   Multithreaded   |   Multi-threaded (/MT)   |
| 动态库（DLL）、Debug  |   Debug Multithread DLL (/libs:dll /threads /dbglibs)    |  Multi-threaded Debug DLL (/MDd)  |
| 动态库、Release        |    Multithread DLL (/libs:dll /threads)    |  Multi-threaded DLL (/MD)  |
>CAUTION：
/MD：动态链接多线程库(msvcrt.lib)。使用该选项时，需要用/NODEFAULTLIB选项来忽略掉libc.lib、 libcmt.lib、libcd.lib、libcmtd.lib、msvcrtd.lib库，否则会有链接错误；
/MDd：动态链接多线程调试库(msvcrtd.lib)。使用该选项时，需要用/NODEFAULTLIB选项来忽略掉libc.lib、 libcmt.lib、msvcrt.lib、libcd.lib、libcmtd.lib库，否则会有链接错误；
/MT：静态链接多线程库(libcmt.lib)。使用该选项时，需要用/NODEFAULTLIB选项来忽略掉libc.lib、 msvcrt.lib、libcd.lib、libcmtd.lib、msvcrtd.lib库，否则会有链接错误；
/MTd：静态链接多线程调试库(libcmtd.lib)。使用该选项时，需要用/NODEFAULTLIB选项来忽略掉libc.lib、 libcmt.lib、msvcrt.lib、libcd.lib、msvcrtd.lib库，否则会有链接错误。

#### 2.2.2 调用Fortran静态库的时候，库的路径和名称都设置对了，但是一直出现下面这样的连接错误
error LNK2001: unresolved external symbol __imp__DataProcess

如果你的函数的定义像下面这样：
extern "C"  int _declspec(dllimport)  FunctionName()
那很好解决，只要将“_declspec(dllimport)”删除就可以了，因为调用静态库不需要这个声明，但是调用动态库时必须要有这个声明，如果去掉了还是有问题，那请再检查一遍静态库是否包含到项目中。

#### 2.2.3 在Fortran中调用C/C++传进来的回调函数时(运行时)，出现下面的运行时错误
Unhandled exception at 0x00000005 in FortranDllTest.exe: 0xC0000005: Access violation reading location 0x00000005.
那我们首先调试一下看是运行到哪一步出现这样的错误，在看看这一步的参数是否正确，起始一般是程序的堆栈被破坏导致的，很有可能是我们的回调函数的调用约定不正确造成的，这个调用约定只能是__cdecl，不能是__stdcall，否则就会出现上面的错误。

#### 2.2.4 出现IntelliSense: 无法打开 源 文件 "XXXXX.h"
VS2010中包含以前的.h/.cpp文件于现在的工程中，出现IntelliSense: 无法打开 源 文件 "XXXXX.h"，搜寻到一些方法都不适用，比如：设置项目属性->配置属性->C/C++->预编译头->使用 (/Yu)/创建 (/Yc)/不使用预编译头三种方式都不行。虽然提示这样的错误，但是运行程序是成功的，初始化和编译运行好像使用不同的查找路径，在低版本的VS2005/VS2008开发而在高版本VS2010中打开时会遇到这样的问题。其解决办法是：
**项目属性->配置属性->C/C++->常规->附加包含目录->$(ProjectDir)**

### 2.3 需要注意的问题
混合语言编程要注意的问题主要体现在：**函数调用和数据结构的存储。**

#### 2.3.1 函数调用声明
由于Fortran编程语言没有大小写之分，Windows平台下的混合语言编程要注意的主要是大小写的问题。考虑到编译器的差异，可以用下面的方式进行跨平台编程的函数声明。
如2.1例子中的定义可以修改为：
```
 #ifdef __cplusplus
 extern "C" {
 #endif
 extern void _cdecl test1(int x,int y);
 extern void _stdcall test2(int& x,int& y);
 extern int _cdecl add(int x,int y);
 extern int _cdecl multiply(int x,int y);
 extern int _stdcall multiply2(int& x,int& y);
 extern float _cdecl divided(float x,float y);
 #define ChangedFunc divided 
 #ifdef __cplusplus
 }
 #endif
```
这样，就可以在C/C++的程序里面直接调用。因为由于C编译器里面，没有定义__cplusplus这个环境变量，所以C也可以直接使用这个头文件。
通过前面Dependency Walker查看Fortran编译生成的DLL发现，函数名全是小写，这与Fortran不分大小写一律大写的规定不符，不知为何，但是，不管怎样，我们知道了其函数的样子，在C/C++调用的时候，我们便可以用上面10行代码那样，通过#define语句给Fortran函数一个别名，以适应C/C++代码的风格。

#### 2.3.2 字符串的传递问题
Windows平台上的Fortran和C/C++的混合语言编程里，字符串的处理需要特别注意。Fortran的一个字符变量是定长的字符串，没有特别的终止符号，这不像C/C++。关于怎样表示字符、怎样存储它们的长度没有固定的约定。有些编译器把一个字符参数作为一对参数传送给一个程序，其中之一是保存这个串的地址，另一个是保存串的长度。Fortran里面字符串的结束就是靠字符串的长度确定的。
对含有字符串的函数，可以这样处理：
例如函数 void cCharFunction( char &msg );需要定义成：void cCharFunction( char &msg , int len ); 经过上面的define之后，在Fortran中，只需调用CCHARFUNCTION（ MSG ）即可。由于Fortran程序没有明显得字符串结束标志，这样，如果两个字符串连在一起的话，C的程序里就会取到这个连在一起的字符串，因此，最好在C的程序里面，对这个由Fortran程序得到的字符串进行处理，因为，从len这个变量，可以得到字符串长度，截取msg的前len个字符作为这个字符串的应有长度。
而如果是在Fortran程序里面，如函数：SUBROUTINE FCHARFUNC(FCHAR)；经过相应的声明，进行下面的定义即可：


在这三种语言的混合编程里，还有一个小问题就是指针的问题。Fortran里面所有的变量都相当于C/C++里面的指针，所以，在C/C++里面的程序里，函数的参数应一律声明成指针的形式（除了字符串参数后面的长度）。
数据：混合编程里，数据上存在的差异也必须引起足够的重视。这体现在两个方面，数组和结构。
数组：Fortran语言里面，数组和C/C++里面的数组有些不同，这表现在两个方面，一是行列顺序，二是数组起始值。
Fortran语言不同于C/C++的行优先，而使用列优先的方式。假设一个A数组，m行n列，那么采用行优先时的数据存放格式为：
a11,a12,…,a1n,a21,a22,…,a2n,……，am1,am2,…，amn
而采用列优先的数据存放格式为：
a11,a21,…,am1,a12,a22,…,am2,……，a1n,a2n,…，amn
行优先顺序推广到多维数组，规定为先排最右的下标；列优先顺序推广到多维数组，规定为先排最左的下标。这样，在混合语言编程里调用数据时，必须注意行列优先的差别，进行准确的调用。
数组的另一个差别是起始下标的不同。Fortran里面，默认的数组下标是以1开始的，而C/C++里面是从0开始的，所以，在调用里面要注意加一或者减一，以保证调用到正确的数据。
结构：在Fortran语言里的结构经过声明后，就被分配了空间，在C/C++里面也要声明它，
采用下面的方式：
```
Fortran：
COMMON /COLOR7/ C_RED, C_GREEN, C_BLUE
COMMON /NDDAT/  NID(NASIZE),XN(3,NASIZE)

C/C++：
#ifdef __cplusplus
extern "C" {
#endif
#define color7 COLOR7
#define nddat NDDAT
extern struct {float c_red; float c_green; float c_blue;} color7;
extern struct {int nid[NASIZE]; float xn[NASIZE][3];}  nddat; 
#ifdef __cplusplus
}
#endif
```
2 Linux平台
Linux平台的混合语言编程和Windows平台上的基本没有什么区别，主要是在define上的不同。考虑到编译器的差异，在函数声明上，可以用下面的方式进行跨平台编程的函数声明。（ C/C++编译器使用GNU gcc，Fortran编译器使用 pgi Fortran ）。
假设一个C的函数为 void cFunction(); 那么，只需要在它的头文件里面进行定义即可：
```
#ifdef  __cplusplus
extern “C” void {
#endif
extern void CFunction();
＃define cFunction cfunction_
#ifdef __cplusplus
}
#endif
```
这样，在Fortran或者C++的程序里面就可以直接调用了。
注意：函数名应不大于31个字符。(即cfuntion_字符长度不大于32字符。PGI&Linux)
同样，对于C++和Fortran里面的函数，声明的时候，也只要改成小写，加下划线即可。

对于数组来说，变化和Windows是一致的。都是行列优先顺序不同的。而对于字符串来说，则不需要额外的注意，gcc编译器会处理好这个问题，也就是并不需要作出额外的改变。

数据结构的定义，也要改成小写加下划线的方式，如：
```
Fortran：
COMMON /COLOR7/ C_RED, C_GREEN, C_BLUE
COMMON /NDDAT/  NID(NASIZE),XN(3,NASIZE)

C/C++：
#ifdef __cplusplus
extern "C" {
#endif
#define color7 color7_
#define nddat nddat_
extern struct {float c_red; float c_green; float c_blue;} color7;
extern struct {int nid[NASIZE]; float xn[NASIZE][3];}  nddat; 
#ifdef __cplusplus
}
#endif
```
3 其它平台
对于Solaris平台，基本上和Linux平台完全一致，但是，考虑到Solaris大多运行在Sparc CPU上，它是采用big endian的，而基本的Windows和Linux运行在Intel或者AMD的X86平台，都是采用little endian的，这一点需要特别注意，这在读写数据文件时，应该给予足够的重视。其它的UNIX平台如HP UNIX，ULTRIX，IRIS等，一般都只有define上的微小差别，在字符串处理、结构及数组方面基本与Linux相同，对它们来说，考虑更多的应该是中央处理器的不同带来的差别。（如对齐、大端和小端）。
WIN32 平台define a A
ULTRIX || SPARC || IRIS || LINUX 平台 define a a_
HPUX || AIX 平台 勿须define 
4 C/C++/FORTRAN 混合编程中的字符串处理
混编中经常会出现需要传递字符串的情况，而字符串的传递是一个较为麻烦的事情，在Fortran里面，字符串是没有结束符的，但是有长度的概念，也就是，编译器里面会给每一个字符串一个长度，以控制字符串的长度。但是这个长度参数在不同的平台下，其位置也是不同的（有的直接跟在字符串后面，有的则跟在函数参数的最后面），对于常见的平台如Windows，Linux, Solaris, HP UNIX, IRIS, 可以用如下方法定义：

例如 c函数
```
void messag( char &msg1, int &where1, char &msg2, int &where2 )
{
printf(“ ……%s should be %d, while %s should be %d\n”, msg1, &where1, msg2, where2);
}
```

如果要在Fortran里面调用的话，需要以下define：
```
#if defined ULTRIX || SPARC || IRIS || LINUX || WIN32
#if defined ULTRIX || SPARC || IRIS || LINUX
extern void __stdcall messag(char&, int&, char&, int&, int, int)
#define messag( s1, i1, s2, i2 ) messag_( s1, i1, s2, i2, strlen(s1), strlen(s2) )
#else  /& WIN32 Platform &/
extern void __stdcall messag(char&, int, int&, char&, int, int&)
#define messag( s1, i1, s2, i2 ) MESSAGE( s1, strlen(s1), i1, s2, strlen(s2), i2 )
#endif
#else  /& Other Platform &/
extern void __stdcall messag(char&, int&, char&, int&, int, int)
#define messag( s1, i1, s2, i2 ) messag( s1, i1, s2, i2, strlen(s1), strlen(s2) )
#endif

如果用在C＋＋中，加上相应的
#ifdef __cplusplus
extern “C” {
#endif

/& your extern code &/

#ifdef __cplusplus
}
#endif
```
Fortran里面便可以直接调用，如：
```
CALL MESSAG(char1, i1, char2,i2)
```
同样，在Fortran里面写的字符串处理函数，使用以上的Define和extern后，也可以在c里面直接调用。
5 文件读写
文件的读写也是混编中一个非常重要的问题，通常的问题发生于不同平台下的混编，以及不同Fortran编译器编译。
在FORTRAN中，文件的写入是由write语句完成的，而每一个write语句可一次性写入多个数据，构成一个数据块。而每一个无格式数据块都由下面3部分组成如图1所示：(1)数据块的开始标志，记录所有数据所占的字节数；(2)组成该数据块的各数据内容。整型数和浮点数，均占4个字节，低字节在前，高字节在后。各数据之间不空格。(3)每个数据块的结束标志，也为该数据块的字节数，而不是以回车换行符作为结束标志。各记录之间也没有分隔符。
 
除此之外，由于编程语言的差异，不同的编译器存储的格式也存在差异，如Visual　FORTRAN与Digital FORTRAN在存储数据块中还存在着差别。差别在于在一个write语句中，Visual Fortran存储数据块的开始与结束标志是用一个字节表示，而在Digital Fortran在是用一个整形数，即四个字节来表示。如图2即Visual Fortran一个数据块最多可以存储2^7(128个字节)，如果一个write语句要求写入的数据量大于128字节时，则按|80|..DATA..|80|80|…DATA…| 80|循环存入。所以在读取时，可以把它转化为Digital FORTRAN的存储形式。

[返回目录](#目录)

## 3  C++中实现Fortran接口
### 3.1 链接
C++中允许函数重载，即函数名相同，形参不同（形参个数、类型或顺序），在编译时，函数重载通常是通过名称修改（name mangling）来实现的，比如在函数名后添加参数类型。
而Fortran不允许函数重载，因此Fortran编译器不会进行name mangling，为了使C++编译器认识Fortran编译的代码，使用SUBROUTINE和FUNCTION时，需关闭name mangling，因为SUBROUTINE和FUNCTION宏均包括 extern “C”。

### 3.2 调用
C++和Fortran的另一区别是调用机制，比如参数如何进入调用堆栈，谁负责函数调用结束后清理堆栈，调用函数还是被调用函数？而且，是否有名称修饰（如函数名前后的下划线）、大小写是否敏感等问题也属于这个讨论范畴。
C/C++采用的是缺省调用约定是__cdecl，Fortran则是__stdcall。在C/C++程序中，可以在函数原型的声明中使用__stdcall关键字来指明过程采用STDCALL调用约定，即extern “C” {void _stdcall FuncName( );}。
Fortran过程采用的缺省标识符是，全部大写的过程名加上“_”前缀和“@n”后缀。在C程序中保留标识符的大小写。编译程序会给采用STDCALL约定的过程标识符加上“_”前缀和“@n”后缀。而添加适应伪注释!DIR$ ATTRIBUTES C,DLLEXPORT::add后生成的DLL函数中只存在函数名为add的函数，ADD 和_ADD@8 均不存在。（**推荐采用STDCALL+REFERENCE的方式**）

### 3.3 C++中Fortran规范定义
为了方便C++程序中隐式调用Fortran库，将可能用到的函数调用声明、宏定义等写在一个FORTRAN.h头文件中，如需调用SUBROUTINE、FUNCTION，其格式一般如下：
```
#include <FORTRAN.h> 
SUBROUTINE f77cls();
REAL_FUNCTION rfunc1(REAL&);
```
此头文件中，对常用的数据类型也进行了定义，具体如下：
```
typedef int     INTEGER;             // INTEGER              4 bytes
typedef float   REAL;                 // REAL                 4 bytes
typedef double  DOUBLE_PRECISION;  // DOUBLE PRECISION    8 bytes
typedef int     LOGICAL;             // LOGICAL              4 bytes
```

### 3.4 C++中调用Fortran需要的类
根据Fortran中字符串、COMPLEX、数组等的特性，编写了一些类，便于C++调用。主要有CHARACTER、COMPLEX、FMATRIX、FOSTREAM，分别用于操作字符串、实数虚数、数组、文件输出。

![](https://github.com/qualitydog/pic/blob/master/pic/fig11.png)

### 3.5 混合编程流程
有了以上的知识储备和简单训练之后，便可以着手C++/Fortran混合编程啦。基本流程可以归纳如下：

1、在IVF下，新建动态链接库工程，添加Fortran源码，分析源码子过程SUBROUTINE和FUNCTION，添加合适的预编译语句，并编译生成DLL和LIB文件；

2、新建C++工程，设置VC++目录下的库目录以包含IVF和其他依赖库；

3、将Fortran编译生成的LIB文件添加至工程，把DLL、LIB文件复制进C++工程的Debug文件夹下；

4、添加FORTRAN.h、FCHAR.h、FCMPLX.h、FMATRIX.h等头文件，并编写Fortran函数的头文件；

5、开始C++ Coding吧。。。

[返回目录](#目录)
