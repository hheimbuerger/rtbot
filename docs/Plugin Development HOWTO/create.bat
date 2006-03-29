@echo This batch requires Xalan-J (http://xml.apache.org/xalan-j/) and FOP
@echo (http://xmlgraphics.apache.org/fop/) in the classpath, javac and fop.bat in
@echo the path and an installed Acrobat that is associated with PDF files to run.
@echo ===============================

@echo Compiling transforming application...
@javac Transform.java
@IF errorlevel 1 GOTO abort

@echo Processing XML and XSL to XSL-FO...
@java Transform PluginDevHowto.xsl PluginDevHowto.xml PluginDevHowto.fo
@IF errorlevel 1 GOTO abort

@echo Processing XSL-FO to PDF...
@call fop PluginDevHowto.fo PluginDevHowto.pdf
@IF errorlevel 1 GOTO abort

@echo Opening PDF...
.\PluginDevHowto.pdf

:abort
