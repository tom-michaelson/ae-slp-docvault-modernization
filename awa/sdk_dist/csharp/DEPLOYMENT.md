# Deployment Instructions for Awa.Client NuGet Package

## Prerequisites

1. **NuGet Account**: Create an account at [nuget.org](https://nuget.org)
2. **API Key**: Generate an API key from your NuGet.org account settings
3. **.NET SDK**: Ensure .NET 8.0 SDK is installed
4. **PowerShell Core**: For cross-platform build script (PowerShell 7+ recommended)

## Building the Package

### Using the Cross-Platform Build Script (Recommended)
```powershell
# Basic build and package
./build-nuget.ps1

# Build with specific version
./build-nuget.ps1 -Version "1.2.3"

# Build and publish to NuGet.org
./build-nuget.ps1 -Publish -ApiKey "YOUR_API_KEY"

# Build and publish to private feed
./build-nuget.ps1 -Publish -ApiKey "YOUR_API_KEY" -Source "https://your-feed.com"

# Auto-increment version and publish
./build-nuget.ps1 -IncrementVersion patch -Publish -ApiKey "YOUR_API_KEY"
```

### Manual Build
```bash
# Clean previous builds
dotnet clean -c Release

# Build and create package
dotnet pack -c Release
```

### Legacy Scripts (Platform-Specific)
```bash
# On macOS/Linux
./publish-nuget.sh YOUR_API_KEY

# On Windows
publish-nuget.bat YOUR_API_KEY
```

## Publishing to NuGet.org

### Option 1: Using the cross-platform build script (Recommended)
```powershell
# Build and publish in one step
./build-nuget.ps1 -Publish -ApiKey "YOUR_API_KEY"

# With version increment
./build-nuget.ps1 -IncrementVersion patch -Publish -ApiKey "YOUR_API_KEY"

# With specific version
./build-nuget.ps1 -Version "1.2.3" -Publish -ApiKey "YOUR_API_KEY"
```

### Option 2: Using legacy scripts
```bash
# macOS/Linux
./publish-nuget.sh YOUR_API_KEY

# Windows
publish-nuget.bat YOUR_API_KEY
```

### Option 3: Manual publishing
```bash
# Find the generated package
ls bin/Release/*.nupkg

# Push to NuGet.org
dotnet nuget push bin/Release/Awa.Client.1.0.0.nupkg --api-key YOUR_API_KEY --source https://api.nuget.org/v3/index.json
```

## Publishing to Private Feed

### Using the cross-platform build script (Recommended)
```powershell
# Build and publish to private feed
./build-nuget.ps1 -Publish -ApiKey "YOUR_API_KEY" -Source "https://your-private-feed.com/api/v2/package"

# With version increment
./build-nuget.ps1 -IncrementVersion patch -Publish -ApiKey "YOUR_API_KEY" -Source "https://your-feed.com"
```

### Using legacy scripts
```bash
# Using script with custom source
./publish-nuget.sh YOUR_API_KEY https://your-private-feed.com/api/v2/package

# Manual push to private feed
dotnet nuget push bin/Release/Awa.Client.1.0.0.nupkg --api-key YOUR_API_KEY --source https://your-private-feed.com/api/v2/package
```

## Version Management

### Automatic Version Management (Recommended)
The cross-platform build script provides automatic version management:

```powershell
# Increment patch version (1.0.0 → 1.0.1)
./build-nuget.ps1 -IncrementVersion patch

# Increment minor version (1.0.0 → 1.1.0)
./build-nuget.ps1 -IncrementVersion minor

# Increment major version (1.0.0 → 2.0.0)
./build-nuget.ps1 -IncrementVersion major

# Set specific version
./build-nuget.ps1 -Version "1.2.3"
```

### Manual Version Management
1. **Update version** in `Awa.Client.csproj`:
   ```xml
   <Version>1.0.1</Version>
   <PackageVersion>1.0.1</PackageVersion>
   <AssemblyVersion>1.0.1.0</AssemblyVersion>
   <FileVersion>1.0.1.0</FileVersion>
   ```

2. **Update version** in `AwaClient.cs`:
   ```csharp
   public static string Version => "1.0.1";
   ```

3. **Rebuild and republish**

## Package Contents

The generated NuGet package includes:
- ✅ Compiled library (.dll)
- ✅ Symbol package (.snupkg) for debugging
- ✅ XML documentation
- ✅ README.md
- ✅ Package metadata (description, tags, etc.)

## Installation by Consumers

Once published, consumers can install the package:

```bash
# Using .NET CLI
dotnet add package Awa.Client

# Using Package Manager Console
Install-Package Awa.Client
```

## Troubleshooting

### Common Issues

1. **Package already exists**: Increment the version number
2. **Invalid API key**: Verify the API key is correct and has push permissions
3. **Network issues**: Check your internet connection and NuGet feed accessibility

### Validation

After publishing, verify the package is available:
1. Search for "Awa.Client" on [nuget.org](https://nuget.org)
2. Check package details and dependencies
3. Test installation in a new project

## Security Notes

- **Never commit API keys** to version control
- **Use environment variables** for API keys in CI/CD
- **Consider using nuget.config** for private feeds
- **Enable package signing** for production packages
