' Abre el servidor DHP sin que la ventana se cierre al instante si hay error
Set WshShell = CreateObject("WScript.Shell")
scriptDir = Replace(WScript.ScriptFullName, WScript.ScriptName, "")
batPath = scriptDir & "scripts\iniciar_streamlit.bat"
If Not CreateObject("Scripting.FileSystemObject").FileExists(batPath) Then
    MsgBox "No se encontro iniciar_streamlit.bat en:" & vbCrLf & scriptDir, vbCritical, "DHP"
    WScript.Quit 1
End If
WshShell.CurrentDirectory = scriptDir
WshShell.Run "cmd /k """ & batPath & """", 1, False
