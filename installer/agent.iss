; Unity AI Assistant - 로컬 캡처 에이전트 설치 프로그램 (Inno Setup 스크립트)
;
; 사전 준비: dist\UnityAIAssistantAgent.exe 가 먼저 있어야 한다.
;   pip install -r requirements.txt
;   pyinstaller --onefile --windowed --name UnityAIAssistantAgent agent_entry.py
;
; 컴파일:
;   1) Inno Setup(무료, https://jrsoftware.org/isinfo.php) 설치
;   2) 이 파일을 Inno Setup Compiler로 열어 Build > Compile, 또는
;      "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" installer\agent.iss
;   결과물: dist_installer\UnityAIAssistantAgentSetup.exe — Unity 개발자들에게 배포 가능한
;   단일 설치 파일 (더블클릭 → 다음 → 다음 → 설치, Python/venv 설치 불필요).

#define MyAppName "Unity AI Assistant Agent"
#define MyAppVersion "1.0.0"
#define MyAppExeName "UnityAIAssistantAgent.exe"

[Setup]
AppId={{5B6C6F1E-2A4A-4C2E-9B4A-UNITYAIASSIST}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\dist_installer
OutputBaseFilename=UnityAIAssistantAgentSetup
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startupicon"; Description: "Windows 시작 시 자동 실행"; GroupDescription: "추가 옵션:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} 제거"; Filename: "{uninstallexe}"
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "설치 후 바로 실행"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 페어링 토큰(agent_config.json)은 사용자 데이터라 제거 시 남겨둔다 — 재설치 시 다시
; 기기 승인을 받지 않아도 되도록. 완전히 지우려면 %APPDATA%\UnityAIAssistant를 수동 삭제.
