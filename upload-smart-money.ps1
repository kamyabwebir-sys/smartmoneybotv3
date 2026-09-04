param(
    [string]$ProjectPath = "C:\Work\smartmoneybotv3",
    [string]$RemoteUrl = "https://github.com/kamyabwebir-sys/smartmoneybotv3.git",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

Write-Host "شروع آپلود پوشه src/smart_money ..." -ForegroundColor Cyan

# بررسی نصب بودن Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git نصب نیست یا در PATH قرار ندارد."
}

# بررسی مسیر پروژه
if (-not (Test-Path $ProjectPath -PathType Container)) {
    throw "پوشه پروژه پیدا نشد: $ProjectPath"
}

Set-Location $ProjectPath

# بررسی پوشه smart_money
$SmartMoneyPath = Join-Path $ProjectPath "src\smart_money"

if (-not (Test-Path $SmartMoneyPath -PathType Container)) {
    throw "پوشه src\smart_money پیدا نشد: $SmartMoneyPath"
}

# اگر Git repository وجود ندارد، ایجادش کن
if (-not (Test-Path (Join-Path $ProjectPath ".git") -PathType Container)) {
    Write-Host "Git repository وجود ندارد؛ ایجاد می‌شود..." -ForegroundColor Yellow
    git init
}

# تنظیم نام و ایمیل محلی، فقط اگر قبلاً تنظیم نشده باشد
$GitUserName = git config user.name
if ([string]::IsNullOrWhiteSpace($GitUserName)) {
    git config user.name "SmartMoneyBot Developer"
}

$GitUserEmail = git config user.email
if ([string]::IsNullOrWhiteSpace($GitUserEmail)) {
    git config user.email "smartmoneybotv3@users.noreply.github.com"
}

# بررسی remote فعلی
$ExistingRemote = git remote get-url origin 2>$null

if ([string]::IsNullOrWhiteSpace($ExistingRemote)) {
    Write-Host "Remote به GitHub اضافه می‌شود..." -ForegroundColor Yellow
    git remote add origin $RemoteUrl
}
elseif ($ExistingRemote -ne $RemoteUrl) {
    Write-Host "Remote فعلی با آدرس موردنظر فرق دارد:" -ForegroundColor Yellow
    Write-Host "فعلی:   $ExistingRemote"
    Write-Host "موردنظر: $RemoteUrl"

    $Answer = Read-Host "آیا remote به آدرس موردنظر تغییر کند؟ (y/n)"

    if ($Answer -eq "y") {
        git remote set-url origin $RemoteUrl
    }
    else {
        throw "عملیات متوقف شد تا به repository اشتباه push نشود."
    }
}

# تنظیم branch
git branch -M $Branch

# فقط پوشه smart_money را اضافه کن
Write-Host "افزودن src/smart_money به Git..." -ForegroundColor Cyan
git add -- "src/smart_money"

# نمایش فایل‌های آماده commit
Write-Host ""
Write-Host "فایل‌هایی که قرار است commit شوند:" -ForegroundColor Green
git diff --cached --name-status

# اگر تغییری وجود ندارد، متوقف شو
$StagedChanges = git diff --cached --name-only

if ([string]::IsNullOrWhiteSpace($StagedChanges)) {
    Write-Host "تغییر جدیدی در src/smart_money وجود ندارد." -ForegroundColor Yellow
    exit 0
}

# Commit
$CommitMessage = "Upload smart_money source package"

git commit -m $CommitMessage

# Push
Write-Host "ارسال به GitHub..." -ForegroundColor Cyan
git push -u origin $Branch

Write-Host ""
Write-Host "آپلود با موفقیت انجام شد." -ForegroundColor Green
Write-Host "Repository: $RemoteUrl"
Write-Host "Branch: $Branch"
Write-Host "Path: src/smart_money"
