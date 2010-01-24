@echo This batch requires Xalan-J (http://xml.apache.org/xalan-j/) and FOP
@echo (http://xmlgraphics.apache.org/fop/) in the classpath, javac and fop.bat in
@echo the path and an installed Acrobat that is associated with PDF files to run.
@echo ===============================

@echo Compiling transforming application...
@javac Transform.java
@IF errorlevel 1 GOTO abort

@echo Processing XML and XSL to XSL-FO...
@java Transform Test.xsl Test.xml Test.html
@IF errorlevel 1 GOTO abort

@echo Processing XSL-FO to PDF...
@REM call fop Test.fo Test.pdf
@REM IF errorlevel 1 GOTO abort

@echo Opening HTML...
@.\Test.html

:abort
