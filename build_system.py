 #!/usr/bin/python

import sys
import os
import os.path
import mimetypes
import string
import argparse
import subprocess
import tarfile
import time
import shutil

verbose=False
PROGNAME="BUILD_SYSTEM"
output="build_all.bat"
IGNOREDIRS = [".git",".metadata"]
TARBALLNAMES = {
    "utilitieslist.txt" : "EPC_utilities" ,
    "unittestlist.txt" : "epc_unit_tests" ,
    "buildlist.txt" : "imc"
}

TARCOMMANDS = {
    "unittestlist.txt" : "MakeTarball.sh -U V0" ,
    "buildlist.txt" : "MakeTarball.sh -T V0"
}

PROGNAME=os.path.abspath( sys.argv[0] )
BUILD_TOOLS_DIR = os.path.dirname( PROGNAME )
TARBALLS_DIR = "TarballLocal"

def ParseCommandLine():
    global verbose
    global output
    global runbatchfile
    global projectslist
    global tarball
    global clean_option
    global tarball_utilities

    parser = argparse.ArgumentParser(prog=PROGNAME,description="Setup build environment")

    parser.add_argument("-v", "--verbose"  , help="Verbose" , action="store_true")
    parser.add_argument('-o', '--output'  , help="Output (batch) file name" , action="store" , default = output )
    parser.add_argument("-r", "--runbatchfile"  , help="run batch file" , action="store_true")
    parser.add_argument("-t", "--tarball" , help="generate tarballs" , action="store_true")
    parser.add_argument("-c", "--clean" , help="clean the projects" , action="store_true")
    parser.add_argument("-T", "--tarball-utilities" , help= "just generate tarball for utilities only" , action="store_true")
    

    parser.add_argument("projectslist", nargs='+', help='Projectlist text files')
    
    args = parser.parse_args()
    if args.verbose:
        verbose = True

    output = args.output
    runbatchfile = args.runbatchfile
    projectslist = args.projectslist
    tarball = args.tarball
    clean_option = args.clean
    tarball_utilities = args.tarball_utilities

    if args.verbose:
        print("Output file name " , output )
        if clean_option:
            print("Will clean the projects. No other options will be effective")
        if runbatchfile:
            print("Will run the script")
        if tarball:
            if runbatchfile:
                print("Will generate tarballs")
            else:
                print("Unless we run the build script, tarballs cannot be generated")

        print("Projects List file " , args.projectslist)

def call_command(command):
    return subprocess.check_call(command, shell=True)
    
def SetExecPermissions(tarinfo):
    tarinfo.mode = 0O777
    return tarinfo



    

def GenerateEnvironmentName( dirname ):
    global outfile
    if dirname in IGNOREDIRS:
        print("Directory " , dirname , " is not required as an environment variable")
    else:
        setenvcmd="set PROJECT_ROOT_%s=%s" % (dirname,os.path.abspath(dirname))
        if verbose:
            print("Command is " , setenvcmd)
        outfile.write(setenvcmd+'\n')

def GenerateBuildCommand(dirname):
    global outfile
    if dirname in IGNOREDIRS:
        print("Directory " , dirname , " is not required as an environment variable")
    else:
        chdircmd="cd %s" % dirname.rstrip()
        outfile.write('\n'+chdircmd+'\n')
        if dirname.find("UnitTest") > 0:
            outfile.write("cmd /C generate_runner.bat .\n")
        outfile.write("make CPULIST=x86 EXCLUDE_VARIANTLIST=g  all\n")


        outfile.write("cd ..\n")

def ProcessProjects( prjlist ):
    if verbose:
        print("-------------------Processing %s\n" % prjlist)

    pf=open(prjlist,'r')
    allprojects=pf.readlines()
    pf.close()

    for p in allprojects:
        if verbose:
            print("=======Project %s" % p)
        GenerateBuildCommand(p)

    print("Basename %s" % os.path.basename(prjlist) )
    tarballname = TARBALLNAMES.get( os.path.basename(  prjlist ).lower() )
    if verbose:
        print("Project : %s will be packed in the tarball %s" % (prjlist,tarballname))

def GenerateTarballs( prjlist ):
    if verbose:
        print("-------------------Processing %s\n" % prjlist)
    
    if os.path.isdir(TARBALLS_DIR):
        print("%s already exists. will cleanup and recreate\n" % TARBALLS_DIR)
        shutil.rmtree(TARBALLS_DIR)
        os.mkdir(TARBALLS_DIR)
    else:
        print("Creating dir %s\n" % TARBALLS_DIR)
        os.mkdir(TARBALLS_DIR)
        
    tarballname=TARBALLNAMES.get( os.path.basename(  prjlist ).lower() )
    if verbose:
        print("Project : %s will be packed in the tarball %s" % (prjlist,tarballname))   

    tarcommand=TARCOMMANDS.get(os.path.basename( prjlist ).lower())
    if tarcommand is not None:
        if verbose:
            print("Project: %s will use the command" % tarcommand )
        tc = os.path.join( BUILD_TOOLS_DIR , tarcommand )
        subprocess.check_call( "sh " + tc , shell=True)
    else:
        if verbose:
            print("Project: %s will use a generic tar packer" % prjlist )
        GenerateTarball(prjlist , tarballname)

def LoadProjects( prjlistfile ):

    pf=open(prjlistfile ,'r')
    allprojects=pf.readlines()
    pf.close()    
    return allprojects

def CleanProject(proj):
    if verbose:
        print("Cleaning %s" % proj )
    wd=os.getcwd()

    #os.chdir( proj )
    cmd="make clean -C %s" % proj
    #os.chdir( wd )
    subprocess.check_call(cmd, shell=True)

def CleanProjects( prjlist ):
    if verbose:
        print("-------------------Processing %s\n" % prjlist)
    allprojects = LoadProjects(prjlist)
    for proj in allprojects:
        prjclean = proj.rstrip()
        CleanProject( prjclean )


def main():
    global outfile
    global clean_option
    global tarball_utilities
    global projectslist

    if clean_option:
        for prjlist in projectslist:
            CleanProjects( prjlist )
        sys.exit(0)

    if tarball_utilities:
        print ("Projects List = " , projectslist)
        for prjlist in projectslist:
            GenerateTarball( prjlist ,TARBALLNAMES.get( os.path.basename(  prjlist ).lower() ) )
        sys.exit(0)

    outfile=open(output,'w')
    listdirs = os.listdir(os.getcwd())
    for dirname in listdirs:
        if os.path.isdir(dirname):
            if verbose:
                print("Directory " , dirname )
            GenerateEnvironmentName( dirname )

    for prjlist in projectslist:
        ProcessProjects( prjlist )  


    outfile.close()
    if runbatchfile:
        subprocess.check_call(output, shell=True)
        if tarball:
            for prjlist in projectslist:
                GenerateTarballs( prjlist )

if __name__ == "__main__":
    ParseCommandLine()
    main()
