java-updater
============

Script to update Oracle's Java. 
Basically it is used to update tar.gz package in Linux Environment.

User executing this script should has writable rights to JAVA directory.
Provided java directory should exist before execution of this command.<br/>
Before use add executable rights to the file:</br>

<code>
	chmod +x java-updater.py
</code>

</br>
Usage: java-updater.py [options]<br/>
Available options:<br/>
<table>
    <thead>
	<tr>
		<td>Parameter</td>
		<td>Description</td>
		<td>Default</td>
	</tr>
    </thead>
	<tr>
		<td>-a, --arch</td>
		<td>Architecture: i586, x64, arm-h, arm-s, sparc, sparcv9</td>
		<td>x64</td>
	</tr>
	<tr>
		<td>-s, --system</td>
		<td>System: linux, solaris, windows, macosx</td>
		<td>linux</td>
	</tr>
	<tr>
		<td>-f, --format</td>
		<td>Format: tar.gz, tar, rpm, exe, bin, dmg, sh, tar.Z</td>
		<td>tar.gz</td>
	</tr>
	<tr>
		<td>-t, --tool</td>
		<td>Java Environment: jdk, jre</td>
		<td>jdk</td>
	</tr>
	<tr>
		<td>-d, --javadir</td>
		<td>JAVA directory in system. Should exists and be writable to user executing this script</td>
		<td>/opt/java</td>
	</tr>
	<tr>
		<td>-n, --newest</td>
		<td>Install newest version of Java found on Oracle's pages</td>
		<td>False</td>
	</tr>
</table>
