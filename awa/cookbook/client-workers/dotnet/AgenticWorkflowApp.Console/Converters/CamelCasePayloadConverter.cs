using System.Text.Json;
using Temporalio.Converters;

namespace AgenticWorkflowApp.Console.Converters;

public class CamelCasePayloadConverter : DefaultPayloadConverter
{
    public CamelCasePayloadConverter()
        : base(new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase })
    {
    }
}
