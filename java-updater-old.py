#!/usr/bin/python
import urllib
import sgmllib
import urllib2
import os, sys
import tarfile
import time
import subprocess
from getopt import getopt, GetoptError

class LinkParser(sgmllib.SGMLParser):

    def __init__(self, verbose=0):
        sgmllib.SGMLParser.__init__(self, verbose)
        self.hyperlinks = []

    def parse(self, content):
        self.feed(content)
        self.close()
        
    def start_a(self, attributes):
        for name, value in attributes:
            if name == "href":
                self.hyperlinks.append(value)

    def getHyperlinks(self):
        return self.hyperlinks

def getPage(link):
    print "Getting content from page:",link
    page = urllib.urlopen(link)
    content = page.read()
    page.close()
    return content

def download(url, destination):
    file_name = url.split('/')[-1]
    u = urllib2.urlopen(url)
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
            status = r"Downloaded: %d kB  [%3.2f%%]" % (size, file_size_dl * 100. / file_size)
        
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
    tarFile = os.path.join(destination,fileName) 
    tar = tarfile.open(tarFile, "r:gz")
    tar.extractall(destination)
    dirName = tar.getnames()[0]
    tar.close()
    time.sleep(1)
    print "Removing file %s"%(tarFile)
    os.remove(tarFile)
    return dirName

def shellcmd(cmd):
    print cmd
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (o,e) = process.communicate()
    print o,e
    return (process.returncode, o, e)

def usage():
    print('\nUsage: java-update [options]\nAvailable options:')
    print("-i, --interactive\t\tChoose JAVA version manually")
    print("-d, --downloadpage \"link\"\tType ORACLE's JAVA download page")
    print("-a, --arch\t\t\tArchitecture: x86, x64")
    print("-s, --system\t\t\tSystem: Linux, Solaris")
    print("-f, --format\t\t\tFormat: tar.gz, rpm")
    print("-t, --tool\t\t\tJAVA: jdk, jre")
    print("-p, --priority\t\t\tPriority in system, example: 1000")
    print("-j, --javadir\t\t\tJAVA directory in system, default: /usr/lib/jvm/\n")
    
    print "Default parameters:"
    print "\tDownload page:\t\t%s"%download_page
    print "\tArchitecture:\t\t%s"%arch
    print "\tSystem:\t\t\t%s"%system
    print "\tDownload file format:\t%s"%fileFormat
    print "\tJAVA directory:\t\t%s"%java_dir
    print "\tJAVA type:\t\t%s"%java_tool
    print "\tPriority:\t\t%s"%priority
    print "\tInteractive mode:\t%s\n"%interactiveMode

if __name__ == "__main__":
    
    #download_page = "http://www.oracle.com/technetwork/java/javase/downloads/"
    download_page = "http://www.oracle.com/technetwork/java/javase/downloads/jdk7-downloads-1880260.html"
    arch = "x64"
    system = "Linux"
    fileFormat = "tar.gz"
    java_dir = "/usr/lib/jvm/"
    java_tool = "jdk"
    priority = 5000
    interactiveMode = False
    appDir = os.path.dirname(os.path.realpath(__file__))
    
    if os.getuid() != 0:
        print "This program should be execute only by root!"
        sys.exit(1)
    
    try:
        opts, args = getopt(sys.argv[1:], 'id:a:s:f:t:p:j:h:', ['interactive','downloadpage=','arch=','system=','format=','tool=','priority=','javadir','help'])
    except GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-i', '--interactive'):
            interactiveMode = True
        elif opt in ('-d', '--downloadpage'):
            download_page = arg
        elif opt in ('-a', '--arch'):
            arch = arg
        elif opt in ('-s', '--system'):
            system = arg
        elif opt in ('-f', '--format'):
            fileFormat = arg
        elif opt in ('-t', '--tool'):
            java_tool = arg
        elif opt in ('-p', '--priority'):
            priority = int(arg)
        elif opt in ('-j', '--javadir'):
            java_dir = arg
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
                   
    #content = getPage(download_page+"index.html")
    content = getPage(download_page)
    
    parser = LinkParser()
    parser.parse(content)
    
    links = parser.getHyperlinks()
    jLinks = {}
    
    print "Searching for Java Runtime Environment hyperlinks..."
    for link in links:
	print link
        searchString = "javase/downloads/jre"
        if java_tool == "jdk":
            searchString = "javase/downloads/jdk"
        if searchString in link:
            urlElements = link.split("/")
            htmlDoc = urlElements[len(urlElements)-1]
            nameElements = htmlDoc.split("-")
            extElements = htmlDoc.split(".")
            jVersion = nameElements[1]
            if jVersion != "netbeans" and extElements[-1] == "html" and nameElements[2] == "download":           
                jLinks[jVersion] = htmlDoc
                print "Found JAVA version: %s -> %s"%(jVersion,htmlDoc)
    
    if (interactiveMode):   
        print "Please choose JAVA version to download or type enter to get the newest available version:"
        i = 1
        for version in jLinks.keys():
            print "%d. %s"%(i,version)
            i += 1
    newestVersion = sorted(set(jLinks.keys()), reverse=True)[0]
    downloadVersion = newestVersion
    print "The newest available JAVA version: %s"%(newestVersion) 
    
    if (interactiveMode):
        option = raw_input(">> ")
        if option.strip() != "":
            try:
                opt = int(option)
                i = 1
                for  version in jLinks.keys():
                    if i == opt:
                        downloadVersion = version
                        break
                    i += 1
            except ValueError:
                print "User type wrong number! Getting the newest version of JAVA!"
            
    
    content = getPage(download_page+jLinks[downloadVersion])
    contentLines = content.split("\n")
    print "Searching download link with parameters:\n\tSystem: %s\n\tArchitecture: %s\n\tFormat: %s"%(system,arch,fileFormat)
    downloadFileDict = {}
    for line in contentLines:
        addLink = False
        if fileFormat == "tar.gz":
            if (fileFormat in line or ("bin" in line and "rpm" not in line)) and system in line and arch in line:
                addLink = True
        elif fileFormat == "rpm":
            if (fileFormat in line or ("bin" in line and "rpm" in line)) and system in line and arch in line:
                addLink = True
        if addLink == True:
            lineElems = line.split(" = ")
            if len(lineElems)>1:
                dictCode = "downloadFileDict = "+lineElems[1]
                exec dictCode
                if downloadFileDict.has_key("filepath"):
                    break
        
    if downloadFileDict.has_key("filepath"):
        print "Downloading file from link: %s Size: %s"%(downloadFileDict["filepath"],downloadFileDict["size"])
        downloadedFile = download(downloadFileDict["filepath"], java_dir)
        print "Extracting file %s"%(downloadedFile)
        if fileFormat == "tar.gz":
            f_ext = downloadedFile.split(".")
            if f_ext[-1] == "gz":
                main_dir = extractFile(downloadedFile, java_dir)
            elif f_ext[-1] == "bin":
                shellcmd("chmod +x %s"%(downloadedFile))
                (rc, o, e) = shellcmd("cd %s; %s"%(java_dir,downloadedFile))
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
        elif fileFormat == "rpm":
            print "Unsupported installation for rpm packages yet! Please install manually file: %s"%(downloadedFile)
            sys.exit(5)
        else:
            print "Bad file format! Please choose correct file format and restart program!"
            sys.exit(3)
                
        jreDir = os.path.join(java_dir,main_dir)
        if arch == "x86":
            archi = "i386"
        elif arch == "x64":
            archi = "amd64"
        else:
            archi = "i386"
            
        subjre = ""
        if java_tool == "jdk":
            subjre = "jre"
        
        print "JAVA was extracted to directory %s"%(jreDir)
        print "Creating jinfo file for new JAVA release"    
        shellcmd("sed s/template/%s/g %s > %s"%(main_dir,os.path.join(appDir,"template-%s-%s"%(java_tool,arch)),os.path.join("%s.%s.jinfo"%(java_dir,main_dir))))
        print "Setting up new Java files"
        shellcmd("cat %s.%s.jinfo | grep -E '^(jre|jdk|plugin)' | awk '{print \"/usr/bin/\" $2 \" \" $2 \" \" $3 \" %s\"}' | xargs -t -n4 update-alternatives --verbose --install"%(java_dir,main_dir,priority))
        shellcmd("update-alternatives --verbose --install /usr/lib/mozilla/plugins/libjavaplugin.so mozilla-javaplugin.so %s %s"%(os.path.join(jreDir,subjre,"lib",archi,"libnpjp2.so"),priority))
        #shellcmd("update-alternatives --verbose --install /usr/lib/xulrunner-addons/plugins/libjavaplugin.so xulrunner-javaplugin.so %s %s"%(os.path.join(jreDir,subjre,"lib",archi,"libnpjp2.so"),priority))
        shellcmd("update-java-alternatives -s %s"%(main_dir))
        print "Finished"
        sys.exit(0)  
    else:
        print "Problem with getting download link. Return Code: -1"
        sys.exit(-1)