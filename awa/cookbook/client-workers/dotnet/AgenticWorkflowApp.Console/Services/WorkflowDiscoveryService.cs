using System.Collections.Concurrent;
using System.Diagnostics;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Schema;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using AgenticWorkflowApp.Console.Models;
using Microsoft.Extensions.Logging;
using Temporalio.Activities;
using Temporalio.Workflows;

namespace AgenticWorkflowApp.Console.Services;

/// <summary>
/// Service for discovering Temporal workflows and activities using reflection, and extracting their metadata.
/// Mirrors the Python loader.py functionality.
/// </summary>
public class WorkflowDiscoveryService
{
    private readonly ILogger<WorkflowDiscoveryService> _logger;
    private readonly JsonSerializerOptions _serializerOptions;
    private readonly JsonSchemaExporterOptions _exporterOptions;

    // Assembly caching for improved startup performance
    private static readonly ConcurrentDictionary<string, Assembly[]> _assemblyCache = new();
    private static readonly object _assemblyCacheLock = new();

    public WorkflowDiscoveryService(ILogger<WorkflowDiscoveryService> logger)
    {
        _logger = logger;

        // Configure serializer options to match our application's settings
        _serializerOptions = CreateSerializerOptions();

        // Configure schema exporter options
        _exporterOptions = new JsonSchemaExporterOptions
        {
            TreatNullObliviousAsNonNullable = true // Treat non-annotated reference types as non-nullable
        };
    }

    /// <summary>
    /// Discover and load all workflows and activities from the specified assemblies.
    /// </summary>
    /// <param name="assemblies">Assemblies to scan for workflows and activities</param>
    /// <returns>Tuple of discovered workflow types and activity methods</returns>
    public (IEnumerable<Type> Workflows, IEnumerable<MethodInfo> Activities) DiscoverWorkflowsAndActivities(Assembly[] assemblies)
    {
        var stopwatch = Stopwatch.StartNew();
        _logger.LogDebug("Starting workflow and activity discovery across {AssemblyCount} assemblies", assemblies.Length);

        var workflows = new List<Type>();
        var activities = new List<MethodInfo>();

        foreach (var assembly in assemblies)
        {
            try
            {
                _logger.LogDebug("Scanning assembly: {AssemblyName}", assembly.GetName().Name);

                var assemblyWorkflows = ScanAssemblyForWorkflows(assembly);
                var assemblyActivities = ScanAssemblyForActivities(assembly);

                workflows.AddRange(assemblyWorkflows);
                activities.AddRange(assemblyActivities);
            }
            catch (Exception ex)
            {
                var assemblyName = assembly.GetName().Name;
                _logger.LogWarning(ex, "Failed to scan assembly {AssemblyName}: {ErrorMessage}",
                    assemblyName, ex.Message);

                // Fail fast for ALL assemblies - no assembly scanning failures should be ignored
                throw new InvalidOperationException($"Failed to scan assembly '{assemblyName}' for workflows and activities: {ex.Message}", ex);
            }
        }

        // De-duplicate workflows and activities
        var uniqueWorkflows = workflows.Distinct().ToList();
        var uniqueActivities = activities.Distinct().ToList();

        stopwatch.Stop();
        _logger.LogInformation("Discovery completed in {ElapsedMs}ms: found {WorkflowCount} workflows and {ActivityCount} activities",
            stopwatch.ElapsedMilliseconds, uniqueWorkflows.Count, uniqueActivities.Count);

        if (uniqueWorkflows.Count > 0)
        {
            var workflowNames = uniqueWorkflows.Select(w =>
            {
                var attr = w.GetCustomAttribute<WorkflowAttribute>();
                return attr?.Name ?? w.Name;
            });
            _logger.LogInformation("Discovered workflows: {Workflows}",
                string.Join(", ", workflowNames));
        }

        if (uniqueActivities.Count > 0)
        {
            var activityNames = uniqueActivities.Select(a =>
            {
                var attr = a.GetCustomAttribute<ActivityAttribute>();
                return attr?.Name ?? a.Name;
            });
            _logger.LogInformation("Discovered activities: {Activities}",
                string.Join(", ", activityNames));
        }

        return (uniqueWorkflows, uniqueActivities);
    }

    /// <summary>
    /// Scan an assembly for workflow classes.
    /// </summary>
    /// <param name="assembly">Assembly to scan</param>
    /// <returns>Enumerable of workflow types</returns>
    public IEnumerable<Type> ScanAssemblyForWorkflows(Assembly assembly)
    {
        var workflows = new List<Type>();

        try
        {
            var types = assembly.GetTypes();

            foreach (var type in types)
            {
                if (IsWorkflowClass(type))
                {
                    _logger.LogDebug("Found workflow class: {TypeName} in {AssemblyName}",
                        type.Name, assembly.GetName().Name);
                    workflows.Add(type);
                }
            }
        }
        catch (ReflectionTypeLoadException ex)
        {
            var assemblyName = assembly.GetName().Name;
            var loaderExceptions = ex.LoaderExceptions?.Where(le => le != null).Select(le => le!.Message).ToArray() ?? [];
            var loaderErrors = loaderExceptions.Length > 0 ? string.Join("; ", loaderExceptions) : "Unknown loader errors";

            _logger.LogWarning(ex, "Failed to load types from assembly {AssemblyName}. Loader errors: {LoaderErrors}",
                assemblyName, loaderErrors);

            throw new InvalidOperationException(
                $"Failed to load types from assembly '{assemblyName}'. This indicates missing dependencies or deployment issues. Loader errors: {loaderErrors}", ex);
        }
        catch (Exception ex)
        {
            var assemblyName = assembly.GetName().Name;
            _logger.LogWarning(ex, "Error scanning assembly {AssemblyName} for workflows", assemblyName);
            throw new InvalidOperationException($"Failed to scan assembly '{assemblyName}' for workflows: {ex.Message}", ex);
        }

        return workflows;
    }

    /// <summary>
    /// Scan an assembly for activity methods.
    /// </summary>
    /// <param name="assembly">Assembly to scan</param>
    /// <returns>Enumerable of activity methods</returns>
    public IEnumerable<MethodInfo> ScanAssemblyForActivities(Assembly assembly)
    {
        var activities = new List<MethodInfo>();

        try
        {
            var types = assembly.GetTypes();

            foreach (var type in types)
            {
                var methods = type.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static);

                foreach (var method in methods)
                {
                    if (IsActivityMethod(method))
                    {
                        _logger.LogDebug("Found activity method: {TypeName}.{MethodName} in {AssemblyName}",
                            type.Name, method.Name, assembly.GetName().Name);
                        activities.Add(method);
                    }
                }
            }
        }
        catch (ReflectionTypeLoadException ex)
        {
            var assemblyName = assembly.GetName().Name;
            var loaderExceptions = ex.LoaderExceptions?.Where(le => le != null).Select(le => le!.Message).ToArray() ?? [];
            var loaderErrors = loaderExceptions.Length > 0 ? string.Join("; ", loaderExceptions) : "Unknown loader errors";

            _logger.LogWarning(ex, "Failed to load types from assembly {AssemblyName}. Loader errors: {LoaderErrors}",
                assemblyName, loaderErrors);

            throw new InvalidOperationException(
                $"Failed to load types from assembly '{assemblyName}'. This indicates missing dependencies or deployment issues. Loader errors: {loaderErrors}", ex);
        }
        catch (Exception ex)
        {
            var assemblyName = assembly.GetName().Name;
            _logger.LogWarning(ex, "Error scanning assembly {AssemblyName} for activities", assemblyName);
            throw new InvalidOperationException($"Failed to scan assembly '{assemblyName}' for activities: {ex.Message}", ex);
        }

        return activities;
    }

    /// <summary>
    /// Check if a type is a workflow class (has [Workflow] attribute).
    /// </summary>
    /// <param name="type">Type to check</param>
    /// <returns>True if the type is a workflow class</returns>
    public static bool IsWorkflowClass(Type type)
    {
        return type.IsClass &&
               !type.IsAbstract &&
               type.GetCustomAttribute<WorkflowAttribute>() != null;
    }

    /// <summary>
    /// Check if a method is an activity method (has [Activity] attribute).
    /// </summary>
    /// <param name="method">Method to check</param>
    /// <returns>True if the method is an activity method</returns>
    public static bool IsActivityMethod(MethodInfo method)
    {
        return method.GetCustomAttribute<ActivityAttribute>() != null;
    }

    /// <summary>
    /// Find the [WorkflowRun] method in a workflow class.
    /// </summary>
    /// <param name="workflowType">The workflow class type</param>
    /// <returns>The workflow run method, or null if not found</returns>
    public static MethodInfo? GetWorkflowRunMethod(Type workflowType)
    {
        return workflowType.GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m => m.GetCustomAttribute<WorkflowRunAttribute>() != null);
    }

    /// <summary>
    /// Get the default assemblies to scan for workflows and activities.
    /// Includes the current assembly and any assemblies that reference Temporal types.
    /// Uses caching for improved performance on subsequent calls.
    /// </summary>
    /// <returns>Array of assemblies to scan</returns>
    public static Assembly[] GetDefaultAssembliesToScan()
    {
        const string cacheKey = "default_assemblies";

        // Return cached result if available
        if (_assemblyCache.TryGetValue(cacheKey, out var cachedAssemblies))
        {
            return cachedAssemblies;
        }

        // Use lock to prevent multiple threads from building the same cache
        lock (_assemblyCacheLock)
        {
            // Double-check pattern
            if (_assemblyCache.TryGetValue(cacheKey, out var doubleCheckAssemblies))
            {
                return doubleCheckAssemblies;
            }

            var assemblies = new List<Assembly>();

            // Always include the current assembly
            var currentAssembly = Assembly.GetExecutingAssembly();
            assemblies.Add(currentAssembly);

            // Include the entry assembly if different
            var entryAssembly = Assembly.GetEntryAssembly();
            if (entryAssembly != null && entryAssembly != currentAssembly)
            {
                assemblies.Add(entryAssembly);
            }

            // Include any referenced assemblies that might contain workflows/activities
            var referencedAssemblies = currentAssembly.GetReferencedAssemblies()
                .Where(name => !name.Name?.StartsWith("System") == true &&
                              !name.Name?.StartsWith("Microsoft") == true &&
                              !name.Name?.StartsWith("Temporalio") == true)
                .Select(name =>
                {
                    try
                    {
                        return Assembly.Load(name);
                    }
                    catch
                    {
                        return null;
                    }
                })
                .Where(a => a != null)
                .Cast<Assembly>();

            assemblies.AddRange(referencedAssemblies);

            var result = assemblies.Distinct().ToArray();

            // Cache the result
            _assemblyCache.TryAdd(cacheKey, result);

            return result;
        }
    }

    /// <summary>
    /// Creates standard JsonSerializerOptions used throughout the application.
    /// This ensures consistency between serialization and schema generation.
    /// </summary>
    private static JsonSerializerOptions CreateSerializerOptions()
    {
        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            WriteIndented = true,
            // Match the behavior expected by Python/AWA
            PropertyNameCaseInsensitive = true,
            // Required for JsonSchemaExporter
            TypeInfoResolver = new DefaultJsonTypeInfoResolver()
        };

        return options;
    }

    /// <summary>
    /// Extract metadata from a workflow type and build WorkflowInfo directly.
    /// </summary>
    /// <param name="workflowType">The workflow class type</param>
    /// <param name="taskQueue">Task queue for the workflow</param>
    /// <returns>WorkflowInfo containing extracted information</returns>
    public Models.WorkflowInfo ExtractWorkflowInfo(Type workflowType, string taskQueue)
    {
        try
        {
            // Get the workflow name from the [Workflow] attribute
            var workflowAttribute = workflowType.GetCustomAttribute<WorkflowAttribute>();
            if (workflowAttribute == null)
            {
                throw new InvalidOperationException($"Type {workflowType.Name} does not have a [Workflow] attribute");
            }

            var workflowName = workflowAttribute.Name ?? workflowType.Name;

            // Find the [WorkflowRun] method
            var runMethod = GetWorkflowRunMethod(workflowType);
            if (runMethod == null)
            {
                throw new InvalidOperationException($"Workflow {workflowType.Name} does not have a [WorkflowRun] method");
            }

            // Get module name (assembly + namespace)
            var moduleName = GetModuleName(workflowType);

            // Extract parameters from the run method
            var parameterInfo = ExtractMethodParameterInfo(runMethod);
            var parametersSchema = FormatMethodParameters(parameterInfo, runMethod);

            _logger.LogDebug("Extracted workflow info for {WorkflowName}: {ParameterCount} parameters",
                workflowName, parameterInfo.Count);

            return new Models.WorkflowInfo
            {
                Name = workflowName,
                ClassName = workflowType.Name,
                Module = moduleName,
                Parameters = parametersSchema,
                Queues = [taskQueue],
                WorkflowType = workflowType
            };
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to extract metadata from workflow {WorkflowType}", workflowType.Name);
            throw;
        }
    }

    /// <summary>
    /// Extract metadata from an activity method and build ActivityInfo directly.
    /// </summary>
    /// <param name="activityMethod">The activity method</param>
    /// <param name="taskQueue">Task queue for the activity</param>
    /// <returns>ActivityInfo containing extracted information</returns>
    public Models.ActivityInfo ExtractActivityInfo(MethodInfo activityMethod, string taskQueue)
    {
        try
        {
            // Get the activity name from the [Activity] attribute
            var activityAttribute = activityMethod.GetCustomAttribute<ActivityAttribute>();
            if (activityAttribute == null)
            {
                throw new InvalidOperationException($"Method {activityMethod.Name} does not have an [Activity] attribute");
            }

            var activityName = activityAttribute.Name ?? activityMethod.Name;

            // Get module name (assembly + namespace of containing type)
            var moduleName = GetModuleName(activityMethod.DeclaringType!);

            // Extract parameters from the method
            var parameterInfo = ExtractMethodParameterInfo(activityMethod);
            var parametersSchema = FormatMethodParameters(parameterInfo, activityMethod);

            _logger.LogDebug("Extracted activity info for {ActivityName}: {ParameterCount} parameters",
                activityName, parameterInfo.Count);

            return new Models.ActivityInfo
            {
                Name = activityName,
                MethodName = activityMethod.Name,
                ClassName = activityMethod.DeclaringType!.Name,
                Module = moduleName,
                Parameters = parametersSchema,
                Queues = [taskQueue],
                Method = activityMethod
            };
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to extract metadata from activity {ActivityMethod}",
                $"{activityMethod.DeclaringType?.Name}.{activityMethod.Name}");
            throw;
        }
    }

    /// <summary>
    /// Generate JSON schema from a C# type.
    /// </summary>
    /// <param name="type">The type to generate schema for</param>
    /// <returns>JSON object representing the schema</returns>
    public JsonObject GenerateJsonSchema(Type type)
    {
        return GenerateSchemaUsingExporter(type);
    }

    /// <summary>
    /// Generate JSON schema using the built-in JsonSchemaExporter.
    /// </summary>
    /// <param name="type">The type to generate schema for</param>
    /// <returns>JSON object representing the schema</returns>
    private JsonObject GenerateSchemaUsingExporter(Type type)
    {
        // Generate schema using JsonSchemaExporter
        var schemaNode = _serializerOptions.GetJsonSchemaAsNode(type, _exporterOptions);

        // JsonSchemaExporter should always return JsonObject for type schemas
        if (schemaNode is not JsonObject jsonObject)
        {
            throw new InvalidOperationException($"Expected JsonObject for type '{type.Name}', but got {schemaNode?.GetType().Name ?? "null"}");
        }

        return jsonObject;
    }


    private JsonObject FormatMethodParameters(List<Models.ParameterInfo> parameterInfo, MethodInfo method)
    {
        return parameterInfo.Count switch
        {
            0 => GenerateEmptyObjectSchema(),
            1 => GenerateSingleParameterSchema(parameterInfo.First()),
            _ => GenerateMultipleParametersSchema(parameterInfo)
        };
    }

    private JsonObject GenerateEmptyObjectSchema()
    {
        return GenerateJsonSchema(typeof(EmptyObject));
    }

    private JsonObject GenerateSingleParameterSchema(Models.ParameterInfo parameter)
    {
        if (parameter.ParameterType == null)
        {
            throw new InvalidOperationException($"Parameter {parameter.Name} has no type information");
        }

        // For single parameter, return its schema directly (Temporal convention)
        return GenerateJsonSchema(parameter.ParameterType);
    }

    private JsonObject GenerateMultipleParametersSchema(List<Models.ParameterInfo> parameterInfo)
    {
        // Start with a base object schema from JsonSchemaExporter
        var baseSchema = GenerateJsonSchema(typeof(Dictionary<string, object>));

        // Build properties and required fields
        var properties = new JsonObject();
        var requiredFields = new List<string>();

        foreach (var param in parameterInfo)
        {
            ValidateParameterType(param);

            // Use JsonSchemaExporter for each parameter's type
            properties[param.Name] = GenerateJsonSchema(param.ParameterType!);
            requiredFields.Add(param.Name);
        }

        // Replace the Dictionary properties with our specific parameter properties
        baseSchema["properties"] = properties;
        if (requiredFields.Count > 0)
        {
            baseSchema["required"] = JsonValue.Create(requiredFields.ToArray());
        }

        return baseSchema;
    }

    private static void ValidateParameterType(Models.ParameterInfo param)
    {
        if (param.ParameterType == null)
        {
            throw new InvalidOperationException($"Parameter {param.Name} has no type information");
        }
    }

    /// <summary>
    /// Empty object type for generating schema for parameterless methods
    /// </summary>
    private class EmptyObject { }

    private List<Models.ParameterInfo> ExtractMethodParameterInfo(MethodInfo method)
    {
        return method.GetParameters()
            .Select(p => new Models.ParameterInfo
            {
                Name = p.Name!,
                TypeString = FormatTypeAnnotation(p.ParameterType),
                ParameterType = p.ParameterType
            })
            .ToList();
    }

    private string GetModuleName(Type type)
    {
        var assemblyName = type.Assembly.GetName().Name ?? "Unknown";
        var namespaceName = type.Namespace ?? "Unknown";
        return $"{assemblyName}.{namespaceName}";
    }

    private string FormatTypeAnnotation(Type type)
    {
        // Handle nullable types
        var underlyingType = Nullable.GetUnderlyingType(type);
        if (underlyingType != null)
        {
            return $"{FormatTypeAnnotation(underlyingType)}?";
        }

        // Handle generic types
        if (type.IsGenericType)
        {
            var typeName = type.Name.Substring(0, type.Name.IndexOf('`'));
            var genericArgs = type.GetGenericArguments()
                .Select(FormatTypeAnnotation);
            return $"{typeName}<{string.Join(", ", genericArgs)}>";
        }

        // Return simple name for non-generic types
        return type.Name;
    }

    /// <summary>
    /// Build WorkflowInfo objects from discovered workflow types.
    /// </summary>
    /// <param name="workflowTypes">Discovered workflow types</param>
    /// <param name="taskQueue">Task queue for the workflows</param>
    /// <returns>List of WorkflowInfo objects</returns>
    public List<Models.WorkflowInfo> BuildWorkflowInfoList(
        IEnumerable<Type> workflowTypes,
        string taskQueue)
    {
        var workflowInfoList = new List<Models.WorkflowInfo>();

        foreach (var workflowType in workflowTypes)
        {
            try
            {
                var workflowInfo = ExtractWorkflowInfo(workflowType, taskQueue);
                workflowInfoList.Add(workflowInfo);
                _logger.LogDebug("Built workflow info for {WorkflowName}", workflowInfo.Name);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to build workflow info for {WorkflowType}", workflowType.Name);
                throw new InvalidOperationException($"Failed to build workflow info for '{workflowType.Name}'. This indicates a critical issue with workflow metadata extraction that must be resolved.", ex);
            }
        }

        _logger.LogInformation("Built {WorkflowCount} workflow info objects", workflowInfoList.Count);
        return workflowInfoList;
    }

    /// <summary>
    /// Build ActivityInfo objects from discovered activity methods.
    /// </summary>
    /// <param name="activityMethods">Discovered activity methods</param>
    /// <param name="taskQueue">Task queue for the activities</param>
    /// <returns>List of ActivityInfo objects</returns>
    public List<Models.ActivityInfo> BuildActivityInfoList(
        IEnumerable<MethodInfo> activityMethods,
        string taskQueue)
    {
        var activityInfoList = new List<Models.ActivityInfo>();

        foreach (var activityMethod in activityMethods)
        {
            try
            {
                var activityInfo = ExtractActivityInfo(activityMethod, taskQueue);
                activityInfoList.Add(activityInfo);
                _logger.LogDebug("Built activity info for {ActivityName}", activityInfo.Name);
            }
            catch (Exception ex)
            {
                var methodSignature = $"{activityMethod.DeclaringType?.Name}.{activityMethod.Name}";
                _logger.LogWarning(ex, "Failed to build activity info for {ActivityMethod}", methodSignature);
                throw new InvalidOperationException($"Failed to build activity info for '{methodSignature}'. This indicates a critical issue with activity metadata extraction that must be resolved.", ex);
            }
        }

        _logger.LogInformation("Built {ActivityCount} activity info objects", activityInfoList.Count);
        return activityInfoList;
    }

    /// <summary>
    /// Build both workflow and activity info lists in one operation.
    /// </summary>
    /// <param name="workflows">Discovered workflow types</param>
    /// <param name="activities">Discovered activity methods</param>
    /// <param name="taskQueue">Task queue for registration</param>
    /// <returns>Tuple of workflow and activity info lists</returns>
    public (List<Models.WorkflowInfo> Workflows, List<Models.ActivityInfo> Activities) BuildWorkflowAndActivityInfo(
        IEnumerable<Type> workflows,
        IEnumerable<MethodInfo> activities,
        string taskQueue)
    {
        _logger.LogInformation("Building workflow and activity metadata...");

        var workflowInfoList = BuildWorkflowInfoList(workflows, taskQueue);
        var activityInfoList = BuildActivityInfoList(activities, taskQueue);

        _logger.LogInformation("Metadata building completed: {WorkflowCount} workflows, {ActivityCount} activities",
            workflowInfoList.Count, activityInfoList.Count);

        // Log the actual registered names (from attributes)
        if (workflowInfoList.Count > 0)
        {
            _logger.LogInformation("Built workflows with attribute names: {WorkflowNames}",
                string.Join(", ", workflowInfoList.Select(w => $"'{w.Name}'")));
        }

        if (activityInfoList.Count > 0)
        {
            _logger.LogInformation("Built activities with attribute names: {ActivityNames}",
                string.Join(", ", activityInfoList.Select(a => $"'{a.Name}'")));
        }

        return (workflowInfoList, activityInfoList);
    }

    /// <summary>
    /// Discover workflows and activities, then build their info objects in one operation.
    /// This is the main entry point that combines discovery and metadata building.
    /// </summary>
    /// <param name="assemblies">Assemblies to scan</param>
    /// <param name="taskQueue">Task queue for registration</param>
    /// <returns>Tuple of workflow and activity info lists</returns>
    public (List<Models.WorkflowInfo> Workflows, List<Models.ActivityInfo> Activities) DiscoverAndBuildWorkflowInfo(
        Assembly[] assemblies,
        string taskQueue)
    {
        _logger.LogInformation("Starting workflow discovery and info building...");

        // Step 1: Discover workflows and activities
        var (workflows, activities) = DiscoverWorkflowsAndActivities(assemblies);

        // Step 2: Build info objects
        var (workflowInfoList, activityInfoList) = BuildWorkflowAndActivityInfo(workflows, activities, taskQueue);

        _logger.LogInformation("Discovery and building completed: {WorkflowCount} workflows, {ActivityCount} activities",
            workflowInfoList.Count, activityInfoList.Count);

        return (workflowInfoList, activityInfoList);
    }
}
