'# MWS Version: Version 2022.5 - Jun 03 2022 - ACIS 31.0.1 -

'# length = mm
'# frequency = GHz
'# time = ns
'# frequency range: fmin = 1.0 fmax = 2.0
'# created = '[VERSION]2022.5|31.0.1|20220603[/VERSION]


'@ Define Parameters

'[VERSION]2022.5|31.0.1|20220603[/VERSION]
Dim cstRt6d05c3d16367StatusFile As String
Dim cstRt6d05c3d16367ArmFile As String
Dim cstRt6d05c3d16367Armed As Boolean
Dim cstRt6d05c3d16367FileNumber As Integer
Dim cstRt6d05c3d16367ErrorNumber As Long
Dim cstRt6d05c3d16367ErrorDescription As String
cstRt6d05c3d16367StatusFile = GetProjectPath("Temp") & "\cst-runtime-6d05c3d163674d51971a2c289e028f43.status"
cstRt6d05c3d16367ArmFile = GetProjectPath("Temp") & "\cst-runtime-6d05c3d163674d51971a2c289e028f43.arm"
On Error Resume Next
cstRt6d05c3d16367Armed = (Dir$(cstRt6d05c3d16367ArmFile) <> "")
If cstRt6d05c3d16367Armed Then Kill cstRt6d05c3d16367ArmFile
On Error GoTo 0
On Error GoTo CSTRuntimeError6d05c3d16367
Dim names(1 To 1) As String
Dim values(1 To 1) As String
names(1) = "pytest_length"
values(1) = "10"
StoreParameters names, values
If cstRt6d05c3d16367Armed Then
cstRt6d05c3d16367FileNumber = FreeFile
Open cstRt6d05c3d16367StatusFile For Output As #cstRt6d05c3d16367FileNumber
Print #cstRt6d05c3d16367FileNumber, "OK"
Close #cstRt6d05c3d16367FileNumber
End If
GoTo CSTRuntimeDone6d05c3d16367
CSTRuntimeError6d05c3d16367:
cstRt6d05c3d16367ErrorNumber = Err.Number
cstRt6d05c3d16367ErrorDescription = Err.Description
On Error Resume Next
If cstRt6d05c3d16367Armed Then
cstRt6d05c3d16367FileNumber = FreeFile
Open cstRt6d05c3d16367StatusFile For Output As #cstRt6d05c3d16367FileNumber
Print #cstRt6d05c3d16367FileNumber, "ERROR"
Print #cstRt6d05c3d16367FileNumber, CStr(cstRt6d05c3d16367ErrorNumber)
Print #cstRt6d05c3d16367FileNumber, ""
Print #cstRt6d05c3d16367FileNumber, cstRt6d05c3d16367ErrorDescription
Print #cstRt6d05c3d16367FileNumber, "0"
Close #cstRt6d05c3d16367FileNumber
End If
On Error GoTo 0
If Not cstRt6d05c3d16367Armed Then ReportError cstRt6d05c3d16367ErrorDescription
CSTRuntimeDone6d05c3d16367:

'@ define frequency range

'[VERSION]2022.5|31.0.1|20220603[/VERSION]
Dim cstRte16c4c29e2c3StatusFile As String
Dim cstRte16c4c29e2c3ArmFile As String
Dim cstRte16c4c29e2c3Armed As Boolean
Dim cstRte16c4c29e2c3FileNumber As Integer
Dim cstRte16c4c29e2c3ErrorNumber As Long
Dim cstRte16c4c29e2c3ErrorDescription As String
cstRte16c4c29e2c3StatusFile = GetProjectPath("Temp") & "\cst-runtime-e16c4c29e2c343439ece1e02dcb9ef52.status"
cstRte16c4c29e2c3ArmFile = GetProjectPath("Temp") & "\cst-runtime-e16c4c29e2c343439ece1e02dcb9ef52.arm"
On Error Resume Next
cstRte16c4c29e2c3Armed = (Dir$(cstRte16c4c29e2c3ArmFile) <> "")
If cstRte16c4c29e2c3Armed Then Kill cstRte16c4c29e2c3ArmFile
On Error GoTo 0
On Error GoTo CSTRuntimeErrore16c4c29e2c3
Solver.FrequencyRange "1.0", "2.0"
If cstRte16c4c29e2c3Armed Then
cstRte16c4c29e2c3FileNumber = FreeFile
Open cstRte16c4c29e2c3StatusFile For Output As #cstRte16c4c29e2c3FileNumber
Print #cstRte16c4c29e2c3FileNumber, "OK"
Close #cstRte16c4c29e2c3FileNumber
End If
GoTo CSTRuntimeDonee16c4c29e2c3
CSTRuntimeErrore16c4c29e2c3:
cstRte16c4c29e2c3ErrorNumber = Err.Number
cstRte16c4c29e2c3ErrorDescription = Err.Description
On Error Resume Next
If cstRte16c4c29e2c3Armed Then
cstRte16c4c29e2c3FileNumber = FreeFile
Open cstRte16c4c29e2c3StatusFile For Output As #cstRte16c4c29e2c3FileNumber
Print #cstRte16c4c29e2c3FileNumber, "ERROR"
Print #cstRte16c4c29e2c3FileNumber, CStr(cstRte16c4c29e2c3ErrorNumber)
Print #cstRte16c4c29e2c3FileNumber, ""
Print #cstRte16c4c29e2c3FileNumber, cstRte16c4c29e2c3ErrorDescription
Print #cstRte16c4c29e2c3FileNumber, "0"
Close #cstRte16c4c29e2c3FileNumber
End If
On Error GoTo 0
If Not cstRte16c4c29e2c3Armed Then ReportError cstRte16c4c29e2c3ErrorDescription
CSTRuntimeDonee16c4c29e2c3:

'@ define boundary

'[VERSION]2022.5|31.0.1|20220603[/VERSION]
Dim cstRt384820c43829StatusFile As String
Dim cstRt384820c43829ArmFile As String
Dim cstRt384820c43829Armed As Boolean
Dim cstRt384820c43829FileNumber As Integer
Dim cstRt384820c43829ErrorNumber As Long
Dim cstRt384820c43829ErrorDescription As String
cstRt384820c43829StatusFile = GetProjectPath("Temp") & "\cst-runtime-384820c438294b9e9d1d8d41d4274843.status"
cstRt384820c43829ArmFile = GetProjectPath("Temp") & "\cst-runtime-384820c438294b9e9d1d8d41d4274843.arm"
On Error Resume Next
cstRt384820c43829Armed = (Dir$(cstRt384820c43829ArmFile) <> "")
If cstRt384820c43829Armed Then Kill cstRt384820c43829ArmFile
On Error GoTo 0
On Error GoTo CSTRuntimeError384820c43829
With Boundary
.Xmin "expanded open"
.Xmax "expanded open"
.Ymin "expanded open"
.Ymax "expanded open"
.Zmin "expanded open"
.Zmax "expanded open"
.Xsymmetry "none"
.Ysymmetry "none"
.Zsymmetry "none"
End With
If cstRt384820c43829Armed Then
cstRt384820c43829FileNumber = FreeFile
Open cstRt384820c43829StatusFile For Output As #cstRt384820c43829FileNumber
Print #cstRt384820c43829FileNumber, "OK"
Close #cstRt384820c43829FileNumber
End If
GoTo CSTRuntimeDone384820c43829
CSTRuntimeError384820c43829:
cstRt384820c43829ErrorNumber = Err.Number
cstRt384820c43829ErrorDescription = Err.Description
On Error Resume Next
If cstRt384820c43829Armed Then
cstRt384820c43829FileNumber = FreeFile
Open cstRt384820c43829StatusFile For Output As #cstRt384820c43829FileNumber
Print #cstRt384820c43829FileNumber, "ERROR"
Print #cstRt384820c43829FileNumber, CStr(cstRt384820c43829ErrorNumber)
Print #cstRt384820c43829FileNumber, ""
Print #cstRt384820c43829FileNumber, cstRt384820c43829ErrorDescription
Print #cstRt384820c43829FileNumber, "0"
Close #cstRt384820c43829FileNumber
End If
On Error GoTo 0
If Not cstRt384820c43829Armed Then ReportError cstRt384820c43829ErrorDescription
CSTRuntimeDone384820c43829:

'@ Define Brick:pytest_baseline_brick

'[VERSION]2022.5|31.0.1|20220603[/VERSION]
Dim cstRt071b410b149eStatusFile As String
Dim cstRt071b410b149eArmFile As String
Dim cstRt071b410b149eArmed As Boolean
Dim cstRt071b410b149eFileNumber As Integer
Dim cstRt071b410b149eErrorNumber As Long
Dim cstRt071b410b149eErrorDescription As String
cstRt071b410b149eStatusFile = GetProjectPath("Temp") & "\cst-runtime-071b410b149e4e469727e4a4aed8094c.status"
cstRt071b410b149eArmFile = GetProjectPath("Temp") & "\cst-runtime-071b410b149e4e469727e4a4aed8094c.arm"
On Error Resume Next
cstRt071b410b149eArmed = (Dir$(cstRt071b410b149eArmFile) <> "")
If cstRt071b410b149eArmed Then Kill cstRt071b410b149eArmFile
On Error GoTo 0
On Error GoTo CSTRuntimeError071b410b149e
With Brick
    .Reset
    .Name "pytest_baseline_brick"
    .Component "component1"
    .Material "PEC"
    .Xrange "0", "pytest_length"
    .Yrange "0", "1"
    .Zrange "0", "1"
    .Create
End With
If cstRt071b410b149eArmed Then
cstRt071b410b149eFileNumber = FreeFile
Open cstRt071b410b149eStatusFile For Output As #cstRt071b410b149eFileNumber
Print #cstRt071b410b149eFileNumber, "OK"
Close #cstRt071b410b149eFileNumber
End If
GoTo CSTRuntimeDone071b410b149e
CSTRuntimeError071b410b149e:
cstRt071b410b149eErrorNumber = Err.Number
cstRt071b410b149eErrorDescription = Err.Description
On Error Resume Next
If cstRt071b410b149eArmed Then
cstRt071b410b149eFileNumber = FreeFile
Open cstRt071b410b149eStatusFile For Output As #cstRt071b410b149eFileNumber
Print #cstRt071b410b149eFileNumber, "ERROR"
Print #cstRt071b410b149eFileNumber, CStr(cstRt071b410b149eErrorNumber)
Print #cstRt071b410b149eFileNumber, ""
Print #cstRt071b410b149eFileNumber, cstRt071b410b149eErrorDescription
Print #cstRt071b410b149eFileNumber, "0"
Close #cstRt071b410b149eFileNumber
End If
On Error GoTo 0
If Not cstRt071b410b149eArmed Then ReportError cstRt071b410b149eErrorDescription
CSTRuntimeDone071b410b149e:

