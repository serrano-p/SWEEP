#!/bin/sh
#toTrace.sh
echo $1
for f in $1/traces_query*.xml; do
	echo $f
	java -jar ../saxon9he.jar -s:$f -xsl:toTrace.xsl -o:$f.mappings.xml
done
exit 0