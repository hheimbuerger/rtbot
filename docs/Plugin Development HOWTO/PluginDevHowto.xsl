<?xml version="1.0"?> 
<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="document">

        <!-- example for a simple fo file. At the beginning the page layout is set.
        Below fo:root there is always
        - a single fo:layout-master-set which defines one or more page layouts
        - an optional fo:declarations,
        - and a sequence of one or more fo:page-sequences containing the text and formatting instructions -->
        <fo:root xmlns:fo="http://www.w3.org/1999/XSL/Format">
        
          <fo:layout-master-set>
        
            <!-- layout for the first page -->
            <fo:simple-page-master master-name="first"
                  page-height="29.7cm"
                  page-width="21cm"
                  margin-top="1cm"
                  margin-bottom="2cm"
                  margin-left="2.5cm"
                  margin-right="2.5cm">
              <fo:region-body margin-top="3cm"/>
              <fo:region-before extent="3cm"/>
              <fo:region-after extent="1.5cm"/>
            </fo:simple-page-master>
        
            <!-- layout for the other pages -->
            <fo:simple-page-master master-name="rest"
                          page-height="29.7cm"
                          page-width="21cm"
                          margin-top="1cm"
                          margin-bottom="2cm"
                          margin-left="2.5cm"
                          margin-right="2.5cm">
              <fo:region-body margin-top="2.5cm"/>
              <fo:region-before extent="2.5cm"/>
              <fo:region-after extent="1.5cm"/>
            </fo:simple-page-master>
        
        <fo:page-sequence-master master-name="basicPSM" >
          <fo:repeatable-page-master-alternatives>
            <fo:conditional-page-master-reference master-reference="first"
              page-position="first" />
            <fo:conditional-page-master-reference master-reference="rest"
              page-position="rest" />
            <!-- recommended fallback procedure -->
            <fo:conditional-page-master-reference master-reference="rest" />
          </fo:repeatable-page-master-alternatives>
        </fo:page-sequence-master>
        
          </fo:layout-master-set>
          <!-- end: defines page layout -->
        
          <!-- actual layout -->
          <fo:page-sequence master-reference="basicPSM">
            <!-- header -->
            <!--
            <fo:static-content flow-name="xsl-region-before">
              <fo:block text-align="end"
                    font-size="10pt"
                    font-family="serif"
                    line-height="14pt" >
                XML Recommendation - p. <fo:page-number/>
              </fo:block>
            </fo:static-content>
            -->
        
            <fo:flow flow-name="xsl-region-body">
                <fo:block
                    font-size="18pt"
                    font-family="sans-serif"
                    line-height="24pt"
                    space-after.optimum="15pt"
                    background-color="blue"
                    color="white"
                    text-align="center"
                    padding-top="3pt"
                    font-variant="small-caps">
                    <xsl:value-of select="@title"/>
                </fo:block>
                <!--<xsl:copy-of select="*|@*|node()"/>-->
                <xsl:apply-templates select="*" />
            </fo:flow>
          </fo:page-sequence>
        </fo:root>
    </xsl:template>

    <xsl:template match="chapter">
        <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format"
            font-size="16pt"
            font-family="sans-serif"
            font-weight="bold"
            line-height="20pt"
            space-before.optimum="10pt"
            space-after.optimum="10pt"
            text-align="start"
            padding-top="3pt">
            <xsl:value-of select="@title"/>
            <xsl:apply-templates select="*" />
        </fo:block>
    </xsl:template>

    <xsl:template match="section">
        <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format"
            font-size="14pt"
            font-family="sans-serif"
            font-weight="normal"
            line-height="20pt"
            space-before.optimum="10pt"
            space-after.optimum="10pt"
            text-align="start"
            padding-top="3pt">
            <xsl:value-of select="@title"/>
            <xsl:apply-templates select="*" />
        </fo:block>
    </xsl:template>

    <xsl:template match="paragraph">
        <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format"
            font-size="12pt"
            font-family="sans-serif"
            font-weight="normal"
            line-height="15pt"
            space-after.optimum="3pt"
            text-align="start">
            <xsl:copy-of select="node()"/>
        </fo:block>
    </xsl:template>

    <xsl:template match="code">
        <!-- table start -->
        <fo:table xmlns:fo="http://www.w3.org/1999/XSL/Format"
          border-width="1pt"
          border-style="solid"
          table-layout="fixed"
          width="100%"
          border-collapse="separate"
          space-before.optimum="8pt"
          space-after.optimum="8pt">
          <fo:table-column column-width="50mm"/>
          <fo:table-body>
            <fo:table-row>
              <fo:table-cell>
                <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format"
                    font-size="10pt"
                    font-family="monospace"
                    line-height="12pt"
                    text-align="start"
                    white-space-collapse="false"
                    linefeed-treatment="preserve"
                    white-space-treatment="preserve">
                    <xsl:copy-of select="node()"/>
                </fo:block>
              </fo:table-cell>
            </fo:table-row>
          </fo:table-body>
        </fo:table>
        <!-- table end -->
    </xsl:template>

<!--
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>
-->
<!--
<xsl:template match="Class">
<BirdInfo>
	<xsl:apply-templates select="Order"/>
</BirdInfo>
</xsl:template>

<xsl:template match="Order">
Order is:  <xsl:value-of select="@Name"/>
	<xsl:apply-templates select="Family"/><xsl:text>
</xsl:text>
</xsl:template>

<xsl:template match="Family">
	Family is:  <xsl:value-of select="@Name"/>
	<xsl:apply-templates select="Species | SubFamily | text()"/>
</xsl:template>

<xsl:template match="SubFamily">
		SubFamily is <xsl:value-of select="@Name"/>
    <xsl:apply-templates select="Species | text()"/>
</xsl:template>

<xsl:template match="Species">
	<xsl:choose>
	  <xsl:when test="name(..)='SubFamily'">
		<xsl:text>	</xsl:text><xsl:value-of select="."/><xsl:text> </xsl:text><xsl:value-of select="@Scientific_Name"/>
	  </xsl:when>
	  <xsl:otherwise>
		<xsl:value-of select="."/><xsl:text> </xsl:text><xsl:value-of select="@Scientific_Name"/>
	  </xsl:otherwise>
	</xsl:choose>
</xsl:template>
-->

</xsl:transform>
