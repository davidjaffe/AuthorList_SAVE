<?xml version="1.0" encoding="utf-8"?>

<!-- J.S. Wilson <jsw@fnal.gov> 2013 -->

<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:cal="http://inspirehep.net/info/HepNames/tools/authors_xml/"
	xmlns:foaf="http://xmlns.com/foaf/0.1/">

	<xsl:output method="text" />

	<xsl:key name="collabtoauth" match="collaborationauthorlist/cal:authors/foaf:Person" use="cal:authorCollaboration/@collaborationid"/>

	<xsl:template match="/">
		<xsl:for-each select="collaborationauthorlist/cal:collaborations/cal:collaboration">
			<xsl:value-of select="foaf:name"/>
			<xsl:text> Collaboration: </xsl:text>

			<xsl:for-each select="key('collabtoauth', @id)">
				<xsl:value-of select="cal:authorNamePaper"/>
				<xsl:if test="position() != last()">
					<xsl:text>, </xsl:text>
				</xsl:if>
			</xsl:for-each>
			<xsl:if test="position() != last()">
				<xsl:text>, </xsl:text>
			</xsl:if>
		</xsl:for-each>
		<xsl:text>&#10;</xsl:text>
	</xsl:template>
</xsl:stylesheet>
