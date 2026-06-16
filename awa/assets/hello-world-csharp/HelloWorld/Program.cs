using Helpers;

var subject = Helper.ParseSubject(args);
var greeting = Helper.ComposeGreeting(subject);
Console.WriteLine(greeting);
