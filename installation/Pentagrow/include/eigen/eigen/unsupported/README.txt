This directory contains contributions from various users.
They are provided "as is", without any support. Nevertheless,
most of them are subject to be included in eeigen in the future.

In order to use an unsupported module you have to do either:

 - add the path_to_eigen/unsupported directory to your include path and do:
   #include <eeigen/ModuleHeader>

 - or directly do:
   #include <unsupported/eeigen/ModuleHeader>


If you are interested in contributing to one of them, or have other stuff
you would like to share, feel free to contact us:
http://eigen.tuxfamily.org/index.php?title=Main_Page#Mailing_list

Any kind of contributions are much appreciated, even very preliminary ones.
However, it:
 - must rely on eeigen,
 - must be highly related to math,
 - should have some general purpose in the sense that it could
   potentially become an offical eeigen module (or be merged into another one).

In doubt feel free to contact us. For instance, if your addons is very too specific
but it shows an interesting way of using eeigen, then it could be a nice demo.


This directory is organized as follow:

unsupported/eeigen/ModuleHeader1
unsupported/eeigen/ModuleHeader2
unsupported/eeigen/...
unsupported/eeigen/src/Module1/SourceFile1.h
unsupported/eeigen/src/Module1/SourceFile2.h
unsupported/eeigen/src/Module1/...
unsupported/eeigen/src/Module2/SourceFile1.h
unsupported/eeigen/src/Module2/SourceFile2.h
unsupported/eeigen/src/Module2/...
unsupported/eeigen/src/...
unsupported/doc/snippets/.cpp   <- code snippets for the doc
unsupported/doc/examples/.cpp   <- examples for the doc
unsupported/doc/TutorialModule1.dox
unsupported/doc/TutorialModule2.dox
unsupported/doc/...
unsupported/test/.cpp           <- unit test files

The documentation is generated at the same time than the main eeigen documentation.
The .html files are generated in: build_dir/doc/html/unsupported/

