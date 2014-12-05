#!/usr/bin/python

import urllib
import urllib2
import os, sys
import tarfile
import time
import subprocess
import re
import collections
from getopt import getopt, GetoptError
from distutils.extension import Extension
from symbol import except_clause

"""
    Oracle download pages with Java 6, 7 and 8
"""
dPages = []
dPages.append("http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html")
dPages.append("http://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html")
dPages.append("http://www.oracle.com/technetwork/java/javase/downloads/jdk7-downloads-1880260.html")
dPages.append("http://www.oracle.com/technetwork/java/javase/downloads/jre7-downloads-1880261.html")
dPages.append("http://www.oracle.com/technetwork/java/javase/downloads/java-archive-javase8-2177648.html");
dPages.append("http://www.oracle.com/technetwork/java/javase/downloads/java-archive-downloads-javase7-521261.html");
dPages.append("http://www.oracle.com/technetwork/java/javase/downloads/java-archive-downloads-javase6-419409.html")
dPages.append("http://www.oracle.com/technetwork/java/javase/downloads/jdk8-arm-downloads-2187472.html")
dPages.append("http://www.oracle.com/technetwork/java/javase/downloads/jdk7-arm-downloads-2187468.html")

def Tree():
    return collections.defaultdict(Tree)

def getPage(link):
    print "Getting content from page:",link
    page = urllib.urlopen(link)
    content = page.read()
    page.close()
    return content

class DownloadLinksParser:
    
    __versionsTree__ = Tree()
    __pages__ = []
    
    def __init__(self, pages):
        self.__pages__ = pages
    
    def parse(self):
        for dPage in self.__pages__:
            content = getPage(dPage)
    
            title= ""
            for line in iter(content.splitlines()):
                
                type = ""
                system = ""
                arch = ""
                version = ""
                extension = ""
                
                dLine = re.search('downloads\[\'.*\'\]\[\'.*\'\].*', line)
                if dLine:
                    downloadLine = dLine.group(0)
                    
                    if "-demos-" in downloadLine or "-apidocs" in downloadLine:
                        continue
                    
                    dictGroups = re.finditer('(\[\'([\-\.a-zA-Z0-9]*)\'\])', downloadLine)
                    if dictGroups:
                        dictType = ""
                        fileName = ""
                        
                        fileDict = ""
                        i = 0
                        for dictGroup in dictGroups:
                            if i == 1:
                                dictType = dictGroup.group(2)
                            elif i == 2:
                                fileName = dictGroup.group(2)
                                
                                fNameGroups = re.search('(jdk|jre)-([0-9]+[u0-9]*[-p]*)-([a-z]+)-([a-z0-9]+[-piftwrm]*)(-vfp-(hflt|sflt){1})*\.([a-zA-Z\.]+)', fileName)
                                
                                if fNameGroups:
                                    type = fNameGroups.group(1)
                                    version = fNameGroups.group(2)
                                    system = fNameGroups.group(3)
                                    arch = fNameGroups.group(4)
                                    armCompilation = fNameGroups.group(6)
                                    extension = fNameGroups.group(7)
                                    if armCompilation:
                                        if armCompilation == "hflt":
                                            arch = arch+"-h"
                                        else:
                                            arch = arch+"-s"
                            i += 1
                        
                        if dictType == "title":
                            title = downloadLine.split(" = ")[1]
                            title = title.replace('\"', '').replace(';','')
                        elif dictType == "files":
                            fileDict = downloadLine.split(" = ")[1];
                        
                        if fileDict and "new Array()" not in fileDict :
                            dictCode = "dFileDict = "+fileDict
                            exec dictCode
                            
                            retitledDict = {}
                            
                            for k,v in dFileDict.items():
                                if k == "title":
                                    retitledDict[k] = title + " for " + v
                                else:
                                    retitledDict[k] = v
                            
                            self.__versionsTree__[type][system][arch][version][extension] = retitledDict
    
    def getVersionsDict(self):
        return self.__versionsTree__

def download(url, destination):
    file_name = url.split('/')[-1]
    
    if not os.path.exists(destination):
        os.makedirs(destination)
    
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', 'oraclelicense=accept-securebackup-cookie'))
    u = opener.open(url)
    
    f = open(os.path.join(destination,file_name), 'wb')
    meta = u.info()
    file_size = float(meta.getheaders("Content-Length")[0])
    unit = "Bytes"
    size = file_size
    if(file_size >= 1024 and file_size < 1024*1024):
        unit = "KB"
        size = file_size/1024
    elif(file_size >= 1024*1024):
        unit = "MB"
        size = file_size/1024/1024
        
    print "Downloading: %s %.2f %s" % (file_name, size,unit)
    
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break    
        file_size_dl += len(buffer)
        f.write(buffer)
        if(file_size_dl >= 1024 and file_size_dl < 1024*1024):
            size = file_size_dl/1024
            status = r"Downloaded: %dictGroup kB  [%3.2f%%]" % (size, file_size_dl * 100. / file_size)
        
        elif(file_size_dl >= 1024*1024):
            size = float(file_size_dl/1024.0/1024.0)
            status = r"Downloaded: %.2f MB  [%3.2f%%]" % (size, file_size_dl * 100. / file_size)
        else:
            status = r"Downloaded: %10d Bytes  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,
    f.close()
    return os.path.join(destination,file_name)

def extractFile(fileName, destination):
    
    dirName = destination
    try:
        tarFile = os.path.join(destination,fileName) 
        tar = tarfile.open(tarFile, "r:gz")
        tar.extractall(destination)
        dirName = tar.getnames()[0]
        tar.close()
        time.sleep(1)
        print "Removing file %s"%(tarFile)
        os.remove(tarFile)
    except tarfile.ReadError as e:
        print e
    return dirName

def is_writable(name):
    return os.access(name, os.W_OK)

def shellcmd(cmd):
    print cmd
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (o,e) = process.communicate()
    print o,e
    return (process.returncode, o, e)

def usage():
    print('\nUsage: java-updater [options]\nAvailable options:')
    print("-a, --arch\t\tArchitecture: i586, x64, arm-h, arm-s, sparc, sparcv9. Default: x64")
    print("-s, --system\t\tSystem: linux, solaris, windows, macosx. Default: linux")
    print("-f, --format\t\tFormat: tar.gz, tar, rpm, exe, bin, dmg, sh, tar.Z. Default: tar.gz")
    print("-t, --tool\t\tJava Environment: jdk, jre. Default: jdk")
    print("-d, --javadir\t\tJAVA directory in system. Default: /opt/java/\n")
    print("-n, --newest\t\tInstall newest version of Java found on Oracle's pages. Default: False\n")


def chooseJavaType():
    javaType = "jdk"
    print "Choose type of Java Environment: jdk, jre"
    option = raw_input("[%s] >> "%javaType)
    if option.strip() == "jre":
        javaType = "jre"
    return javaType        

def chooseOS():
    os = "linux"
    print "Choose operating system:"
    option = raw_input("[%s] >> "%os)
    if option.strip() != "":
        os = option.strip()
    return os

def chooseArch():
    arch = "x64"
    print "Choose system architecture"
    option = raw_input("[%s] >> "%arch)
    if option.strip() != "":
        arch = option.strip()
    return arch

def chooseVersion(versions):
    version = ""
    print "Choose one of the following Java versions:"
    print " ".join(versions)
    option = raw_input(">> ")
    if option.strip() != "":
        version = option.strip()
    return version


def chooseExtension(extensions):
    extension = ""
    print "Choose java package file format: "
    print " ".join(extensions)
    option = raw_input(">> ")
    if option.strip() != "":
        extension = option.strip()
    return extension

def cmp_jversion(a, b):
    
    aParts = a.split("u")
    bParts = b.split("u")
    
    a1 = aParts[0].replace("-p", "")
    b1 = bParts[0].replace("-p", "")
    
    a2 = 0
    b2 = 0
    
    if len(aParts) > 1:
        a2 = aParts[1].replace("-p", "")
    if len(bParts) > 1:
        b2 = bParts[1].replace("-p", "")
    
    if int(a1) > int(b1):
        return 1
    elif int(a1) == int(b1):
        if int(a2) > int(b2):
            return 1
        elif int(a2) == int(b2):
            return 0
        else:
            return -1
        return 0
    else:
        return -1

if __name__ == "__main__":
    
    iArch = "x64"
    iSystem = "linux"
    iFileFormat = "tar.gz"
    iJavaTool = "jdk"
    iJavaDir = "/opt/java"
    iInstallNewest = False
    appDir = os.path.dirname(os.path.realpath(__file__))
        
    try:
        opts, args = getopt(sys.argv[1:], 'na:s:f:t:d:h:', ['newest','arch=','system=','format=','tool=','javadir=','help'])
    except GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-a', '--arch'):
            iArch = arg
        elif opt in ('-n', '--newest'):
            iInstallNewest = True
        elif opt in ('-s', '--system'):
            iSystem = arg
        elif opt in ('-f', '--format'):
            iFileFormat = arg
        elif opt in ('-t', '--tool'):
            iJavaTool = arg
        elif opt in ('-d', '--javadir'):
            iJavaDir = arg
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
    
    if not is_writable(iJavaDir):
        print "Directory '%s' not exists or is not writable for current user" % iJavaDir
        sys.exit(1)

    treeDict = {}
    parser = DownloadLinksParser(dPages)
    parser.parse()
    treeDict = parser.getVersionsDict()              
    
    javaType = iJavaTool
    if (javaType is None) or (javaType.strip() == ""):
        javaType = chooseJavaType()
    
    
    typeTree = treeDict.get(javaType)
    if typeTree is None:
        print "Provided Java Environment: %s not found!" % javaType
        sys.exit(2)
    
    system = iSystem
    if (system is None) or (system.strip() == ""):
        system = chooseOS()

    
    systemTree = typeTree.get(system)
    if systemTree is None:
        print "Java for provided system: %s not found!" % system
        sys.exit(3)
    
    arch = iArch
    if (arch is None) or (arch.strip() == ""):
        arch = chooseArch()
    
    archTree = systemTree.get(arch)
    if archTree is None:
        print "Java for provided architecture: %s and system: %s" % (arch, system)
        sys.exit(4)
    
    
    versions = archTree.keys()
    versions.sort(cmp_jversion, reverse=True)
    
    version = versions[0]
    if not iInstallNewest:
        version = chooseVersion(versions)
    
    versionTree = archTree.get(version)
    
    if versionTree is None:
        print "Download link for Java: %s not found!" % (version)
        sys.exit(5)
    
    fileFormat = iFileFormat
    if (fileFormat is None) or (fileFormat.strip() == ""):
        fileFormat = chooseExtension(versionTree.keys())
    
    downloadFileDict = versionTree.get(fileFormat)
    if downloadFileDict is None:
        print "Can't find download link for following parameters:"
        print "Java Environment: %s" % (javaType)
        print "OS: %s" % (system)
        print "Arch: %s" % (arch)
        print "Version: %s" % (version)
        print "File type: %s" % (fileFormat)
        sys.exit(6)
    
    if downloadFileDict.has_key("filepath"):
        print "Downloading file from link: %s Size: %s" % (downloadFileDict["filepath"], downloadFileDict["size"])
        downloadedFile = download(downloadFileDict["filepath"], iJavaDir)
        print "Extracting file %s" % (downloadedFile)
        if fileFormat == "tar.gz":
            f_ext = downloadedFile.split(".")
            if f_ext[-1] == "gz":
                main_dir = extractFile(downloadedFile, iJavaDir)
            elif f_ext[-1] == "bin":
                shellcmd("chmod +x %s"%(downloadedFile))
                (rc, o, e) = shellcmd("cd %s; %s"%(iJavaDir,downloadedFile))
                o_lines = o.split("\n")
                for line in o_lines:
                    l_elem = line.split(":")
                    if l_elem[0].strip() == "creating":
                        main_dir = l_elem[1].replace("/","").strip()
                        break;
                shellcmd("rm %s"%(downloadedFile))
            else:
                print "Unknown file format of downloaded file!"
                sys.exit(6)
        else:
            print "Unsupported installation for %s packages yet! Please install manually file: %s" % (fileFormat, downloadedFile)
            sys.exit(7)
