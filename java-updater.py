#!/usr/bin/env python2

import urllib
import urllib2
import os
import sys
import tarfile
import time
import subprocess
import re
import collections
from getopt import getopt, GetoptError

"""
    Oracle download pages with Java 6, 7 and 8
"""
f_name_pattern = "(jdk|jre)-([0-9]+[u0-9]*[-p]*)-([a-z]+)-([a-z0-9]+[-piftwrm]*)(-vfp-(hflt|sflt){1})*\.([a-zA-Z\.]+)"
download_pages = [
    "http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html"
]


def object_tree():
    return collections.defaultdict(object_tree)


def get_page(link):
    print "Getting content from page:", link
    page = urllib.urlopen(link)
    content = page.read()
    page.close()
    return content


class DownloadLinksParser:
    
    __versionsTree__ = object_tree()
    __pages__ = []
    
    def __init__(self, pages):
        self.__pages__ = pages
    
    def parse(self):
        for dPage in self.__pages__:
            content = get_page(dPage)
    
            title = ""
            for _line in iter(content.splitlines()):
                
                _type = ""
                _system = ""
                _arch = ""
                _version = ""
                extension = ""
                
                d_line = re.search('downloads\[\'.*\'\]\[\'.*\'\].*', _line)
                if d_line:
                    download_line = d_line.group(0)
                    
                    if "-demos-" in download_line or "-apidocs" in download_line:
                        continue
                    
                    dict_groups = re.finditer('(\[\'([\-\.a-zA-Z0-9]*)\'\])', download_line)
                    if dict_groups:
                        dict_type = ""
                        file_dict = {}
                        i = 0
                        for dict_group in dict_groups:
                            if i == 1:
                                dict_type = dict_group.group(2)
                            elif i == 2:
                                file_name = dict_group.group(2)
                                
                                f_name_groups = re.search(f_name_pattern, file_name)
                                
                                if f_name_groups:
                                    _type = f_name_groups.group(1)
                                    _version = f_name_groups.group(2)
                                    _system = f_name_groups.group(3)
                                    _arch = f_name_groups.group(4)
                                    arm_compilation = f_name_groups.group(6)
                                    extension = f_name_groups.group(7)
                                    if arm_compilation:
                                        if arm_compilation == "hflt":
                                            _arch = _arch+"-h"
                                        else:
                                            _arch = _arch+"-s"
                            i += 1
                        
                        if dict_type == "title":
                            title = download_line.split(" = ")[1]
                            title = title.replace('\"', '').replace(';', '')
                        elif dict_type == "files":
                            file_dict_elements = download_line.split(" = ")
                            if len(file_dict_elements) != 2:
                                file_dict = None
                            else:
                                file_dict = file_dict_elements[1]
                        
                        if file_dict and "new Array()" not in file_dict:
                            dict_code = "file_dict = " + file_dict
                            exec dict_code
                            
                            retitled_dict = {}
                            
                            for k, v in file_dict.items():
                                if k == "title":
                                    retitled_dict[k] = title + " for " + v
                                else:
                                    retitled_dict[k] = v
                            
                            self.__versionsTree__[_type][_system][_arch][_version][extension] = retitled_dict
    
    def get_versions_dict(self):
        return self.__versionsTree__


def download(url, destination):
    file_name = url.split('/')[-1]
    
    if not os.path.exists(destination):
        os.makedirs(destination)
    
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', 'oraclelicense=accept-securebackup-cookie'))
    u = opener.open(url)
    
    f = open(os.path.join(destination, file_name), 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    unit = "Bytes"
    size = file_size
    if 1024*1024 > file_size >= 1024:
        unit = "KB"
        size = file_size/1024
    elif file_size >= 1024*1024:
        unit = "MB"
        size = file_size/1024/1024
        
    print "Downloading: %s %.2f %s" % (file_name, size, unit)
    
    file_size_dl = 0
    block_sz = 8192
    while True:
        _buffer = u.read(block_sz)
        if not _buffer:
            break    
        file_size_dl += len(_buffer)
        f.write(_buffer)
        if 1024*1024 > file_size_dl >= 1024:
            size = file_size_dl / 1024
            status = r"Downloaded: %d kB  [%3.2f%%]" % (size, file_size_dl * 100. / file_size)
        
        elif file_size_dl >= 1024*1024:
            size = float(file_size_dl/1024.0/1024.0)
            status = r"Downloaded: %.2f MB  [%3.2f%%]" % (size, file_size_dl * 100. / file_size)
        else:
            status = r"Downloaded: %10d Bytes  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print(status)
    f.close()
    return os.path.join(destination, file_name)


def extract_file(file_name, destination):
    
    dir_name = destination
    try:
        tar_file = os.path.join(destination, file_name)
        tar = tarfile.open(tar_file, "r:gz")
        tar.extractall(destination)
        dir_name = tar.getnames()[0]
        tar.close()
        time.sleep(1)
        print "Removing file %s" % tar_file
        os.remove(tar_file)
    except tarfile.ReadError as _e:
        print _e
    return dir_name


def is_writable(name):
    return os.access(name, os.W_OK)


def shell_cmd(cmd):
    print(cmd)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (_o, _e) = process.communicate()
    print _o, _e
    return process.returncode, _o, _e


def usage():
    print('\nUsage: java-updater [options]\nAvailable options:')
    print("-a, --arch\t\tArchitecture: i586, x64, arm-h, arm-s, sparc, sparcv9. Default: x64")
    print("-s, --system\t\tSystem: linux, solaris, windows, macosx. Default: linux")
    print("-f, --format\t\tFormat: tar.gz, tar, rpm, exe, bin, dmg, sh, tar.Z. Default: tar.gz")
    print("-t, --tool\t\tJava Environment: jdk, jre. Default: jdk")
    print("-d, --javadir\t\tJAVA directory in system. Default: /opt/java/\n")
    print("-n, --newest\t\tInstall newest version of Java found on Oracle's pages. Default: True\n")


def choose_java_type():
    java_type = "jdk"
    print "Choose type of Java Environment: jdk, jre"
    option = raw_input("[%s] >> " % java_type)
    if option.strip() == "jre":
        java_type = "jre"
    return java_type


def choose_os():
    _os = "linux"
    print "Choose operating system:"
    option = raw_input("[%s] >> " % _os)
    if option.strip() != "":
        _os = option.strip()
    return _os


def choose_arch():
    _arch = "x64"
    print "Choose system architecture"
    option = raw_input("[%s] >> " % _arch)
    if option.strip() != "":
        _arch = option.strip()
    return _arch


def choose_version(_versions):
    _version = ""
    print "Choose one of the following Java versions:"
    print " ".join(_versions)
    option = raw_input(">> ")
    if option.strip() != "":
        _version = option.strip()
    return _version


def choose_extension(extensions):
    extension = ""
    print "Choose java package file format: "
    print " ".join(extensions)
    option = raw_input(">> ")
    if option.strip() != "":
        extension = option.strip()
    return extension


def cmp_jversion(a, b):
    
    a_parts = a.split("u")
    b_parts = b.split("u")
    
    a1 = a_parts[0].replace("-p", "")
    b1 = b_parts[0].replace("-p", "")
    
    a2 = 0
    b2 = 0
    
    if len(a_parts) > 1:
        a2 = a_parts[1].replace("-p", "")
    if len(b_parts) > 1:
        b2 = b_parts[1].replace("-p", "")
    
    if int(a1) > int(b1):
        return 1
    elif int(a1) == int(b1):
        if int(a2) > int(b2):
            return 1
        elif int(a2) == int(b2):
            return 0
        else:
            return -1
    else:
        return -1

if __name__ == "__main__":
    
    iArch = "x64"
    iSystem = "linux"
    iFileFormat = "tar.gz"
    iJavaTool = "jdk"
    iJavaDir = "/opt/java"
    iInstallNewest = True
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
    parser = DownloadLinksParser(download_pages)
    parser.parse()
    treeDict = parser.get_versions_dict()
    
    javaType = iJavaTool
    if (javaType is None) or (javaType.strip() == ""):
        javaType = choose_java_type()

    typeTree = treeDict.get(javaType)
    if typeTree is None:
        print "Provided Java Environment: %s not found!" % javaType
        sys.exit(2)
    
    system = iSystem
    if (system is None) or (system.strip() == ""):
        system = choose_os()

    systemTree = typeTree.get(system)
    if systemTree is None:
        print "Java for provided system: %s not found!" % system
        sys.exit(3)
    
    arch = iArch
    if (arch is None) or (arch.strip() == ""):
        arch = choose_arch()
    
    archTree = systemTree.get(arch)
    if archTree is None:
        print "Java for provided architecture: %s and system: %s" % (arch, system)
        sys.exit(4)

    versions = archTree.keys()
    versions.sort(cmp_jversion, reverse=True)
    
    version = versions[0]
    if not iInstallNewest:
        version = choose_version(versions)
    
    versionTree = archTree.get(version)
    
    if versionTree is None:
        print "Download link for Java: %s not found!" % version
        sys.exit(5)
    
    fileFormat = iFileFormat
    if (fileFormat is None) or (fileFormat.strip() == ""):
        fileFormat = choose_extension(versionTree.keys())
    
    downloadFileDict = versionTree.get(fileFormat)
    if downloadFileDict is None:
        print "Can't find download link for following parameters:"
        print "Java Environment: %s" % javaType
        print "OS: %s" % system
        print "Arch: %s" % arch
        print "Version: %s" % version
        print "File type: %s" % fileFormat
        sys.exit(6)
    
    if "filepath" in downloadFileDict.keys():
        print "Downloading file from link: %s Size: %s" % (downloadFileDict["filepath"], downloadFileDict["size"])
        downloadedFile = download(downloadFileDict["filepath"], iJavaDir)
        print "Extracting file %s" % downloadedFile
        if fileFormat == "tar.gz":
            f_ext = downloadedFile.split(".")
            if f_ext[-1] == "gz":
                main_dir = extract_file(downloadedFile, iJavaDir)
            elif f_ext[-1] == "bin":
                shell_cmd("chmod +x %s" % downloadedFile)
                (rc, o, e) = shell_cmd("cd %s; %s" % (iJavaDir, downloadedFile))
                o_lines = o.split("\n")
                for line in o_lines:
                    l_elem = line.split(":")
                    if l_elem[0].strip() == "creating":
                        main_dir = l_elem[1].replace("/", "").strip()
                        break
                shell_cmd("rm %s" % downloadedFile)
            else:
                print "Unknown file format of downloaded file!"
                sys.exit(6)
        else:
            print "Unsupported installation for %s packages yet! Please install manually file: %s" % (fileFormat,
                                                                                                      downloadedFile)
            sys.exit(7)
