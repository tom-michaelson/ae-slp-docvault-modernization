namespace Helpers;
public static class Helper
{
    public static string? ParseSubject(string[] args)
    {
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--subject" && i + 1 < args.Length)
            {
                return args[i + 1];
            }
        }

        return null;
    }
    public static string ComposeGreeting(string? subject = null)
    {
        subject ??= "World";
        return $"Hello {subject}!";
    }
}
