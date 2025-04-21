# Get the current date and time in UTC
$utcDate = [DateTime]::UtcNow

# Format the date and time in ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ)
$iso8601Time = $utcDate.ToString("o")

# Output the formatted time string
Write-Output $iso8601Time 