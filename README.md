java-updater
============

Script to update Oracle's Java. 
Basically it is used to update tar.gz package in Linux Environment.

Script should be as a root user.<br/>
Before use add executable rights to the file:</br>

<code>
	chmod +x java-updater.py
</code>

</br>
Usage: java-updater.py [options]<br/>
Available options:<br/>
<table>
	<tr>
		<td>-a, --arch</td>
		<td>Architecture: i586, x64, arm-h, arm-s, sparc, sparcv9</td>
	</tr>
	<tr>
		<td>-s, --system</td>
		<td>System: linux, solaris, windows, macosx</td>
	</tr>
	<tr>
		<td>-f, --format</td>
		<td>Format: tar.gz, tar, rpm, exe, bin, dmg, sh, tar.Z</td>
	</tr>
	<tr>
		<td>-t, --tool</td>
		<td>Java Environment: jdk, jre</td>
	</tr>
	<tr>
		<td>-d, --javadir</td>
		<td>JAVA directory in system, default: /usr/java/</td>
	</tr>
	<tr>
		<td>-n, --newest</td>
		<td>Install newest version of Java found on Oracle's pages, default: False</td>
	</tr>
</table>
