import os
from tvhtokodi.files import splitfn, findExtraFile, makeFileList


def test_splitfn():
    pwd = os.getcwd()
    path = os.path.abspath(os.path.join(pwd, "exampledata/emptyfile.ts"))
    xdir, xfile, xext = splitfn(path)
    assert xdir == os.path.abspath(os.path.join(pwd, "exampledata"))
    assert xfile == "emptyfile"
    assert xext == ".ts"


def test_findExtraFile():
    pwd = os.getcwd()
    path = os.path.abspath(os.path.join(pwd, "exampledata/emptyfile.ts"))
    extra = findExtraFile(path, ".txt")
    assert extra == os.path.abspath(os.path.join(pwd, "exampledata/emptyfile.txt"))


def test_findExtraFile_missing():
    pwd = os.getcwd()
    path = os.path.abspath(os.path.join(pwd, "exampledata/2ndemptyfile.ts"))
    extra = findExtraFile(path, ".txt")
    assert extra is None


def test_makeFileList():
    pwd = os.getcwd()
    path = os.path.abspath(os.path.join(pwd, "exampledata/emptyfile.ts"))
    flist = makeFileList(path)
    assert flist == [
        os.path.abspath(os.path.join(pwd, "exampledata/emptyfile.ts")),
        os.path.abspath(os.path.join(pwd, "exampledata/emptyfile.txt")),
    ]


def test_makeFileList_missing():
    pwd = os.getcwd()
    path = os.path.abspath(os.path.join(pwd, "exampledata/2ndemptyfile.ts"))
    flist = makeFileList(path)
    assert flist == [os.path.abspath(os.path.join(pwd, "exampledata/2ndemptyfile.ts"))]
