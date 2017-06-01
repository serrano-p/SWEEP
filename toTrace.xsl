<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xsl:stylesheet [
  <!ENTITY nl "&#xa;">
  <!ENTITY tab "&#x9;">
]>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" exclude-result-prefixes="xs" version="1.0">

    <xsl:output indent="yes" method="xml"/>
    <!-- doctype-system="log.dtd" standalone="no"-->

    <xsl:template name="pattern-xml">
        <xsl:param name="i"/>
        <xsl:choose>
            <xsl:when test="$i[@type = 'iri']">
                <xsl:element name="{name($i)}">
                    <xsl:attribute name="type">iri</xsl:attribute>
                    <xsl:attribute name="val">
                        <xsl:value-of select="$i/@val"/>
                    </xsl:attribute>
                </xsl:element>
            </xsl:when>
            <xsl:when test="$i[@type = 'var']">
                <xsl:element name="{name($i)}">
                    <xsl:attribute name="type">var</xsl:attribute>
                    <xsl:attribute name="val">
                        <xsl:value-of select="name($i)"/>
                    </xsl:attribute>
                </xsl:element>
            </xsl:when>
            <xsl:when test="$i[@type = 'lit']">
                <xsl:element name="{name($i)}">
                    <xsl:attribute name="type">lit</xsl:attribute>
                    <xsl:choose>
                        <xsl:when test="contains($i/text(), '@')">
                            <xsl:attribute name="language">
                                <xsl:value-of select="substring-after($i/text(), '@')"/>
                            </xsl:attribute>
                            <xsl:variable name="r" select="substring-before($i/text(), '@')"/>
                            <xsl:value-of select="substring($r, 2, string-length($r) - 2)"/>
                        </xsl:when>
                        <xsl:when test="contains($i/text(), '^^')">
                            <xsl:attribute name="datatype">
                                <xsl:value-of select="substring-after($i/text(), '^^')"/>
                            </xsl:attribute>
                            <xsl:variable name="r" select="substring-before($i/text(), '^^')"/>
                            <xsl:value-of select="substring($r, 2, string-length($r) - 2)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of
                                select="substring($i/text(), 2, string-length(text()) - 2)"/>
                        </xsl:otherwise>
                    </xsl:choose>

                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$i/@val"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="/">
        <trace>
            <xsl:apply-templates select="/trace/entry"/>
        </trace>
    </xsl:template>

    <xsl:template match="entry">
        <entry client="{@client}" time="{@time}">
            <tp>
                <xsl:call-template name="pattern-xml">
                    <xsl:with-param name="i" select="s"/>
                </xsl:call-template>

                <xsl:call-template name="pattern-xml">
                    <xsl:with-param name="i" select="p"/>
                </xsl:call-template>

                <xsl:call-template name="pattern-xml">
                    <xsl:with-param name="i" select="o"/>
                </xsl:call-template>
            </tp>
            <!--xsl:apply-templates select="/trace/data-triple-N3[@id eq current()/@id]"/-->
            <xsl:if test="s[@type = 'var']">
                <s-mapping>
                    <xsl:apply-templates select="/trace/data-triple-N3[@id = current()/@id]/s"/>
                </s-mapping>
            </xsl:if>
            <xsl:if test="p[@type = 'var']">
                <p-mapping>
                    <xsl:apply-templates select="/trace/data-triple-N3[@id = current()/@id]/p"/>
                </p-mapping>
            </xsl:if>
            <xsl:if test="o[@type = 'var']">
                <o-mapping>
                    <xsl:apply-templates select="/trace/data-triple-N3[@id = current()/@id]/o"/>
                </o-mapping>
            </xsl:if>
        </entry>
    </xsl:template>

    <xsl:template match="data-triple-N3">
        <res>
            <xsl:call-template name="pattern-xml">
                <xsl:with-param name="i" select="s"/>
            </xsl:call-template>

            <xsl:call-template name="pattern-xml">
                <xsl:with-param name="i" select="p"/>
            </xsl:call-template>

            <xsl:call-template name="pattern-xml">
                <xsl:with-param name="i" select="o"/>
            </xsl:call-template>
        </res>
    </xsl:template>

    <xsl:template match="s | o | p">
        <xsl:call-template name="pattern-xml">
            <xsl:with-param name="i" select="."/>
        </xsl:call-template>
    </xsl:template>
</xsl:stylesheet>
