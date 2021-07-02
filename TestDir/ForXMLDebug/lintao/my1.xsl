<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:cal="http://www.slac.stanford.edu/spires/hepnames/authors_xml/"
    xmlns:foaf="http://xmlns.com/foaf/0.1/">

<xsl:template match="/">
    <xsl:text>% Last update: </xsl:text>
    <xsl:value-of select="collaborationauthorlist/cal:creationDate"/>
</xsl:template>
</xsl:stylesheet>

