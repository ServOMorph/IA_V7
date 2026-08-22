param(
    [Parameter(Mandatory=$true)][ValidateSet("bounds","findwindow","screenshot","click","doubleclick","move","paste","key")]
    [string]$Action,
    [int]$X,
    [int]$Y,
    [int]$MinX,
    [int]$MaxX,
    [int]$MinY,
    [int]$MaxY,
    [string]$Text,
    [string]$Key,
    [string]$OutPath
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$definition = @'
using System;
using System.Runtime.InteropServices;

public struct RECT {
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
}

public static class Native {
    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    public static extern void mouse_event(uint dwFlags, int dx, int dy, uint dwData, UIntPtr dwExtraInfo);

    [DllImport("user32.dll")]
    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);

    public const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    public const uint MOUSEEVENTF_LEFTUP = 0x0004;
    public const byte VK_CONTROL = 0x11;
    public const byte VK_V = 0x56;
    public const byte VK_RETURN = 0x0D;
    public const byte VK_ESCAPE = 0x1B;
    public const byte VK_TAB = 0x09;
    public const uint KEYEVENTF_KEYUP = 0x0002;
}
'@
Add-Type -TypeDefinition $definition -Language CSharp

function Assert-InScope {
    param([int]$PosX, [int]$PosY)
    if ($MinX -and $PosX -lt $MinX) {
        throw "Clic refuse : X=$PosX < MinX=$MinX. L'UI doit rester dans sa zone."
    }
    if ($MaxX -and $PosX -gt $MaxX) {
        throw "Clic refuse : X=$PosX > MaxX=$MaxX. L'UI doit rester dans sa zone."
    }
    if ($MinY -and $PosY -lt $MinY) {
        throw "Clic refuse : Y=$PosY < MinY=$MinY. L'UI doit rester dans sa zone."
    }
    if ($MaxY -and $PosY -gt $MaxY) {
        throw "Clic refuse : Y=$PosY > MaxY=$MaxY. L'UI doit rester dans sa zone."
    }
}

switch ($Action) {
    "bounds" {
        $bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
        [PSCustomObject]@{
            Left = $bounds.Left
            Top = $bounds.Top
            Width = $bounds.Width
            Height = $bounds.Height
        } | ConvertTo-Json -Compress
    }
    "findwindow" {
        if (-not $Text) { throw "Le parametre -Text est requis pour l'action findwindow" }
        $proc = Get-Process | Where-Object { $_.MainWindowTitle -match [regex]::Escape($Text) } | Select-Object -First 1
        if (-not $proc) { throw "Fenetre non trouvee pour le titre contenant : $Text" }
        $rect = New-Object RECT
        [Native]::GetWindowRect($proc.MainWindowHandle, [ref]$rect) | Out-Null
        [PSCustomObject]@{
            Title = $proc.MainWindowTitle
            Left = $rect.Left
            Top = $rect.Top
            Right = $rect.Right
            Bottom = $rect.Bottom
        } | ConvertTo-Json -Compress
    }
    "screenshot" {
        $bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
        $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bmp)
        $graphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bmp.Size)
        if (-not $OutPath) {
            $OutPath = Join-Path $env:TEMP ("screenshot_" + (Get-Date -Format "yyyyMMdd_HHmmss_fff") + ".png")
        }
        $bmp.Save($OutPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $graphics.Dispose()
        $bmp.Dispose()
        Write-Output $OutPath
    }
    "move" {
        [Native]::SetCursorPos($X, $Y)
    }
    "click" {
        Assert-InScope -PosX $X -PosY $Y
        [Native]::SetCursorPos($X, $Y)
        Start-Sleep -Milliseconds 100
        [Native]::mouse_event([Native]::MOUSEEVENTF_LEFTDOWN, 0, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Milliseconds 50
        [Native]::mouse_event([Native]::MOUSEEVENTF_LEFTUP, 0, 0, 0, [UIntPtr]::Zero)
    }
    "doubleclick" {
        Assert-InScope -PosX $X -PosY $Y
        [Native]::SetCursorPos($X, $Y)
        for ($i = 0; $i -lt 2; $i++) {
            Start-Sleep -Milliseconds 80
            [Native]::mouse_event([Native]::MOUSEEVENTF_LEFTDOWN, 0, 0, 0, [UIntPtr]::Zero)
            Start-Sleep -Milliseconds 50
            [Native]::mouse_event([Native]::MOUSEEVENTF_LEFTUP, 0, 0, 0, [UIntPtr]::Zero)
        }
    }
    "paste" {
        if (-not $Text) { throw "Le parametre -Text est requis pour l'action paste" }
        Set-Clipboard -Value $Text
        Start-Sleep -Milliseconds 150
        [Native]::keybd_event([Native]::VK_CONTROL, 0, 0, [UIntPtr]::Zero)
        [Native]::keybd_event([Native]::VK_V, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Milliseconds 60
        [Native]::keybd_event([Native]::VK_V, 0, [Native]::KEYEVENTF_KEYUP, [UIntPtr]::Zero)
        [Native]::keybd_event([Native]::VK_CONTROL, 0, [Native]::KEYEVENTF_KEYUP, [UIntPtr]::Zero)
    }
    "key" {
        $vk = switch ($Key) {
            "ENTER" { [Native]::VK_RETURN }
            "ESCAPE" { [Native]::VK_ESCAPE }
            "TAB" { [Native]::VK_TAB }
            default { throw "Touche non supportee : $Key (ENTER, ESCAPE, TAB uniquement)" }
        }
        [Native]::keybd_event($vk, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Milliseconds 50
        [Native]::keybd_event($vk, 0, [Native]::KEYEVENTF_KEYUP, [UIntPtr]::Zero)
    }
}
