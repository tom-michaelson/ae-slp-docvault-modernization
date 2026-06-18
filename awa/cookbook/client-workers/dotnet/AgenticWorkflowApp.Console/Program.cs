using AgenticWorkflowApp.Console.Extensions;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

var host = Host.CreateDefaultBuilder(args)
    .UseContentRoot(Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location)!)
    .ConfigureLogging(ctx => ctx.AddSimpleConsole().SetMinimumLevel(LogLevel.Information))
    .ConfigureServices((context, services) =>
    {
        // Single method call to configure the complete workflow system
        services.AddWorkflowSystem(context.Configuration);
    })
    .Build();

await host.RunAsync();
