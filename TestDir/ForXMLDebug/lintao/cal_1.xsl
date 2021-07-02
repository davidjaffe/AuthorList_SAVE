<?xml version="1.0" encoding="ISO-8859-1"?>

<!-- J.S. Wilson <jsw@fnal.gov> 2013 -->

<xsl:stylesheet version="1.0" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:cal="http://inspirehep.net/info/HepNames/tools/authors_xml/"
	xmlns:foaf="http://xmlns.com/foaf/0.1/"
	xmlns:fn="http://www.w3.org/2005/xpath-functions">

	<xsl:output method="text" />

	<xsl:template name="string-replace-all">
		<xsl:param name="text"/>
		<xsl:param name="replace"/>
		<xsl:param name="by"/>
		<xsl:choose>
			<xsl:when test="contains($text,$replace)">
				<xsl:value-of select="substring-before($text,$replace)"/>
				<xsl:value-of select="$by"/>
				<xsl:call-template name="string-replace-all">
					<xsl:with-param name="text" select="substring-after($text,$replace)"/>
					<xsl:with-param name="replace" select="$replace"/>
					<xsl:with-param name="by" select="$by"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$text"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template name="texfix">
		<xsl:param name="tofix"/>
		<xsl:variable name="tofix1">
			<xsl:call-template name="string-replace-all">
				<xsl:with-param name="text" select="$tofix"/>
				<xsl:with-param name="replace" select="'&amp;'"/>
				<xsl:with-param name="by" select="'\&amp;'"/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="tofix2">
			<xsl:call-template name="string-replace-all">
				<xsl:with-param name="text" select="$tofix1"/>
				<xsl:with-param name="replace" select="'á'"/>
				<xsl:with-param name="by" select='"\&apos;{a}"'/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="tofix3">
			<xsl:call-template name="string-replace-all">
				<xsl:with-param name="text" select="$tofix2"/>
				<xsl:with-param name="replace" select="'é'"/>
				<xsl:with-param name="by" select='"\&apos;{e}"'/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="tofix4">
			<xsl:call-template name="string-replace-all">
				<xsl:with-param name="text" select="$tofix3"/>
				<xsl:with-param name="replace" select="'í'"/>
				<xsl:with-param name="by" select='"\&apos;{i}"'/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="tofix5">
			<xsl:call-template name="string-replace-all">
				<xsl:with-param name="text" select="$tofix4"/>
				<xsl:with-param name="replace" select="'ó'"/>
				<xsl:with-param name="by" select='"\&apos;{o}"'/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="tofix6">
			<xsl:call-template name="string-replace-all">
				<xsl:with-param name="text" select="$tofix5"/>
				<xsl:with-param name="replace" select="'ü'"/>
				<xsl:with-param name="by" select="'\&quot;{u}'"/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="tofix7">
			<xsl:call-template name="string-replace-all">
				<xsl:with-param name="text" select="$tofix6"/>
				<xsl:with-param name="replace" select="'à'"/>
				<xsl:with-param name="by" select="'\&#96;{a}'"/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:value-of select="$tofix7"/>
	</xsl:template>

	<xsl:key name="k1" match="collaborationauthorlist/cal:organizations/foaf:Organization" use="@id"/>
	<xsl:key name="group" match="collaborationauthorlist/cal:organizations/foaf:Organization[cal:group]" use="cal:group/@with"/>

	<xsl:template name="affil">
		<xsl:param name="id"/>
		<xsl:variable name="org" select="key('k1', $id)"/>
		<xsl:if test="not($org/cal:group) and not($org/cal:orgStatus = 'nonmember')">
			<xsl:text>\affiliation{</xsl:text>
			<xsl:choose>
				<xsl:when test="not($org/cal:orgStatus)">
					<xsl:call-template name="texfix">
						<xsl:with-param name="tofix" select="$org/cal:orgAddress"/>
					</xsl:call-template>
					<xsl:if test="key('group',$id) and not($org/cal:orgAddress = '')">
						<xsl:text>: </xsl:text>
					</xsl:if>
					<xsl:for-each select="key('group',$id)">
						<xsl:call-template name="texfix">
							<xsl:with-param name="tofix" select="cal:orgAddress"/>
						</xsl:call-template>
						<xsl:if test="position() != last()">
							<xsl:text>; </xsl:text>
						</xsl:if>
					</xsl:for-each>
				</xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="texfix">
						<xsl:with-param name="tofix" select="$org/cal:orgAddress"/>
					</xsl:call-template>
					<xsl:for-each select="key('group',$id)">
						<xsl:text>, </xsl:text>
						<xsl:text>\ensuremath{^{</xsl:text>
						<xsl:call-template name="orgindex">
							<xsl:with-param name="orgid" select="@id"/>
						</xsl:call-template>
						<xsl:text>}}</xsl:text>
						<xsl:call-template name="texfix">
							<xsl:with-param name="tofix" select="cal:orgAddress"/>
						</xsl:call-template>
					</xsl:for-each>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:text>}&#10;</xsl:text>
		</xsl:if>
	</xsl:template>

	<xsl:template name="orgindex">
		<xsl:param name="orgid"/>
		<xsl:for-each select="/collaborationauthorlist/cal:organizations/foaf:Organization[(cal:orgStatus='nonmember') or (cal:group and (key('k1',cal:group/@with)/cal:orgStatus))]">
			<xsl:sort select="cal:orgStatus" order="descending"/>
			<xsl:if test="(@id = $orgid)">
				<xsl:number format="a" value="position()*(position() &lt;= 26) + (position()-26)*(26+1)*(position() &gt; 26)"/>
			</xsl:if>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="/">
		<xsl:text>% Last update: </xsl:text>
		<xsl:value-of select="collaborationauthorlist/cal:creationDate"/>
		<xsl:text>&#10;</xsl:text>

		<xsl:for-each select="collaborationauthorlist/cal:organizations/foaf:Organization[not(cal:orgStatus!='member')]">
			<xsl:call-template name="affil">
				<xsl:with-param name="id" select="@id"/>
			</xsl:call-template>
		</xsl:for-each>

		<xsl:text>&#10;</xsl:text>
		<xsl:for-each select="collaborationauthorlist/cal:authors/foaf:Person">
			<xsl:sort select='translate(translate(cal:authorNamePaperFamily, "&apos;", ""), "abcdefghijklmnopqrstuvwxyzá","ABCDEFGHIJKLMNOPQRSTUVWXYZA")'/>
			<xsl:sort select='translate(translate(cal:authorNamePaperGiven, "&apos;. ",""), "abcdefghijklmnopqrstuvwxyzá", "ABCDEFGHIJKLMNOPQRSTUVWXYZA")'/>
			<xsl:text>\author{</xsl:text>
			<xsl:call-template name="string-replace-all">
				<xsl:with-param name="text">
					<xsl:call-template name="texfix">
						<xsl:with-param name="tofix" select="cal:authorNamePaper"/>
					</xsl:call-template>
				</xsl:with-param>
				<xsl:with-param name="replace" select="' '"/>
				<xsl:with-param name="by" select="'~'"/>
			</xsl:call-template>
			<xsl:for-each select="cal:authorAffiliations/cal:authorAffiliation">
				<xsl:sort select="@organizationid"/>
				<xsl:variable name="org" select="key('k1',@organizationid)"/>
				<xsl:choose>
					<xsl:when test="$org/cal:orgStatus='nonmember'">
						<xsl:text>\ensuremath{^{</xsl:text>
						<xsl:call-template name="orgindex">
							<xsl:with-param name="orgid" select="$org/@id"/>
						</xsl:call-template>
						<xsl:text>}}</xsl:text>
					</xsl:when>
					<xsl:when test="$org/cal:group">
						<xsl:text>\ensuremath{^{</xsl:text>
						<xsl:call-template name="orgindex">
							<xsl:with-param name="orgid" select="$org/@id"/>
						</xsl:call-template>
						<xsl:text>}}</xsl:text>
					</xsl:when>
				</xsl:choose>
			</xsl:for-each>
			<xsl:text>}&#10;</xsl:text>

			<xsl:if test="cal:authorStatus='Deceased'">
				<xsl:text>\thanks{Deceased}&#10;</xsl:text>
			</xsl:if>

			<xsl:for-each select="cal:authorAffiliations/cal:authorAffiliation">
				<xsl:call-template name="affil">
					<xsl:with-param name="id" select="@organizationid"/>
				</xsl:call-template>
			</xsl:for-each>
		</xsl:for-each>

		<xsl:text>&#10;</xsl:text>
		<xsl:text>\collaboration{</xsl:text>
		<xsl:value-of select="collaborationauthorlist/cal:collaborations/cal:collaboration/foaf:name"/>
		<xsl:text> Collaboration}&#10;</xsl:text>
		<xsl:text>\altaffiliation[With visitors from]{&#10;</xsl:text>
		<xsl:for-each select="collaborationauthorlist/cal:organizations/foaf:Organization[cal:orgStatus='nonmember']">
			<xsl:text>\ensuremath{^{</xsl:text>
			<xsl:call-template name="orgindex">
				<xsl:with-param name="orgid" select="@id"/>
			</xsl:call-template>
			<xsl:text>}}</xsl:text>
			<xsl:call-template name="texfix">
				<xsl:with-param name="tofix" select="./cal:orgAddress"/>
			</xsl:call-template>
			<xsl:if test="position() != last()">
				<xsl:text>,</xsl:text>
			</xsl:if>
			<xsl:text>&#10;</xsl:text>
		</xsl:for-each>
		<xsl:text>}&#10;</xsl:text>
		<xsl:text>\noaffiliation</xsl:text>

		<xsl:text>&#10;</xsl:text>
		<xsl:text>% Last update: </xsl:text>
		<xsl:value-of select="collaborationauthorlist/cal:creationDate"/>
	</xsl:template>
</xsl:stylesheet>

