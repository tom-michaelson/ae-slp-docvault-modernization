class RefineDocumentationPageRequest {
    tech_stack string
    relevant_source_file_name string
    relevant_source_file_content string
    existing_documentation_page string
}

class DocumentationDiff {
    reasoning string @description("1-2 sentences explaining why the diff is needed.")
    diff string @description(#"
        A diff using the context_before, old_content, new_content, and context_after format.
    "#)
}

class RefineDocumentationPageResult {
    diffs DocumentationDiff[]
}

function RefineDocumentationPage(request: RefineDocumentationPageRequest) -> RefineDocumentationPageResult {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}

        You are an expert technical writer. Your task is to review an existing_documentation_page with the additional context of a specific relevant source file. Review the existing_documentation_page and prepare a set of diff edits along the following lines:

        1. Correct any errors or inaccuracies in the existing_documentation_page.
        2. Add any missing critical information to the existing_documentation_page.
        3. Remove any unnecessary or redundant information from the existing_documentation_page.

        IMPORTANT: If no edits are needed, you should return an empty list. DO NOT make up changes that are unnecessary.

        {{ _.role("user") }}

        <tech_stack description="The tech stack of the application.">
        {{ request.tech_stack }}
        </tech_stack>

        <relevant_source_file_name>
        {{request.relevant_source_file_name}}
        </relevant_source_file_name>

        <relevant_source_file_content>
        {{request.relevant_source_file_content}}
        </relevant_source_file_content>

        <existing_documentation_page>
        {{request.existing_documentation_page}}
        </existing_documentation_page>

        # Response

        ## Diff Format

        For each snippet of content that needs to be changed, repeat the following:
        [context_before] -> See below for further instructions on context.
        - [old_content] -> Precede the old content with a minus sign.
        + [new_content] -> Precede the new, replacement content with a plus sign.
        [context_after] -> See below for further instructions on context.

        For instructions on [context_before] and [context_after]:
        - By default, show 3 lines of content immediately above and 3 lines immediately below each change. If a change is within 3 lines of a previous change, do NOT duplicate the first change’s [context_after] lines in the second change’s [context_before] lines.
        - If 3 lines of context is insufficient to uniquely identify the snippet of content within the file, use the @@ operator to indicate the class, function, or header to which the snippet belongs. For instance, we might have:
        @@ class BaseClass
        [3 lines of pre-context]
        - [old_content]
        + [new_content]
        [3 lines of post-context]

        - If a content block is repeated so many times in a class or function such that even a single @@ statement and 3 lines of context cannot uniquely identify the snippet of content, you can use multiple `@@` statements to jump to the right context. For instance:

        @@ class BaseClass
        @@ 	def method():
        [3 lines of pre-context]
        - [old_content]
        + [new_content]
        [3 lines of post-context]

        Note, then, that we do not use line numbers in this diff format, as the context is enough to uniquely identify content. An example of a message that you might pass as "input" to this function, in order to apply a patch, is shown below.

        {{ ctx.output_format }}
    "#
}

test TestClassifyFile {
  functions [RefineDocumentationPage]
  args {
    request {
        tech_stack "tech stack!"
        relevant_source_file_name "my_file.cs"
        relevant_source_file_content #"
        public class MyFile {
            public void MyMethod() {
                Console.WriteLine("Hello, World!");
            }
        }
        "#
        existing_documentation_page "existing!"
    }
  }
}


test TestExecuteTransformUserDefinedRefineDocumentationPageT0a17a {
    functions [RefineDocumentationPage]
    args {
        request     {
            tech_stack #"

      Based on the provided `.csproj` file, I'll create a comprehensive technical stack description for this project.

      ## Backend
      The backend is built using **ASP.NET Core** targeting **.NET 8.0**. This is a modern, cross-platform framework for building web applications and services. The project appears to be a web application with built-in authentication and authorization capabilities through ASP.NET Core Identity.

      ## Database
      The application uses **Microsoft SQL Server** as its database system, as indicated by the `Microsoft.EntityFrameworkCore.SqlServer` package. **Entity Framework Core** serves as the ORM (Object-Relational Mapper), providing database access and management capabilities. The project also includes EF Core Tools for migrations and database management tasks.

      ## Key Libraries & Dependencies
      - **ASP.NET Core Identity**: Provides user authentication, authorization, and account management functionality.
      - **Entity Framework Core**: ORM for database operations with SQL Server integration.
      - **ASP.NET Core Diagnostics for EF Core**: Provides middleware for Entity Framework Core error pages.
      - **Visual Studio Web Code Generation**: Tools for scaffolding controllers, views, and other components.

      ## Other Notable Technologies
      - The project uses **User Secrets** for secure configuration management in development environments, as indicated by the `UserSecretsId` property.
      - **Nullable reference types** are enabled, indicating a focus on preventing null reference exceptions.
      - **Implicit usings** are enabled, which simplifies code by automatically including common namespaces.

      ## Technology Versions

      | Technology | Version |
      |------------|---------|
      | .NET | 8.0 |
      | ASP.NET Core | 8.0 |
      | Entity Framework Core | 7.0.10 |
      | ASP.NET Core Identity | 7.0.10 |
      | ASP.NET Core Identity UI | 7.0.10 |
      | EF Core SQL Server Provider | 7.0.10 |
      | VS Web Code Generation | 8.0.0-rc.1.23461.3 |
            "#
      relevant_source_file_name "source/ToDo/Models/ToDo.cs"
      relevant_source_file_content #"
      using System.ComponentModel.DataAnnotations;

namespace ToDo.Models
{
    public class ToDo
    {

        [Key]
        public int Id { get; set; }

        [Required(ErrorMessage = "Title is required")]
        public string Title { get; set; } = String.Empty;

        [DataType(DataType.MultilineText)]
        public string Details { get; set; } = String.Empty;

        [DataType(DataType.DateTime)]
        public DateTime Date { get; set; }

        [Display(Name = "Is Done")]
        public bool IsDone { get; set; }
    }
}

      "#
      existing_documentation_page #"# Working with EF Core

This documentation provides a comprehensive guide to using Entity Framework Core in the ToDo application. It covers everything from basic concepts to advanced features, helping developers understand how to effectively work with the data access layer.

## EF Core Basics

Entity Framework Core (EF Core) is a lightweight, extensible, and cross-platform version of Entity Framework, Microsoft's object-relational mapping (ORM) framework. In our ToDo application, EF Core serves as the primary data access technology, providing the following key features:

- **Object-Relational Mapping**: Maps C# classes to database tables
- **LINQ Integration**: Enables type-safe querying using LINQ
- **Change Tracking**: Automatically tracks changes to entities
- **Migrations**: Provides tools for evolving the database schema
- **Relationship Management**: Handles entity relationships and navigation properties

Our application uses EF Core 7.0.10 with SQL Server as the database provider, as defined in the project configuration:

```csharp
// From Program.cs
var connectionString = builder.Configuration.GetConnectionString(\"DefaultConnection\") ??
    throw new InvalidOperationException(\"Connection string 'DefaultConnection' not found.\");
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(connectionString));
```

This configuration integrates EF Core with ASP.NET Core's dependency injection system, making the database context available throughout the application.

## DbContext Configuration

The `ApplicationDbContext` class is the cornerstone of our EF Core implementation. It inherits from `IdentityDbContext` to incorporate ASP.NET Core Identity tables while adding our application-specific entities.

```csharp
public class ApplicationDbContext : IdentityDbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<ToDo.Models.ToDo> ToDos { get; set; } = null!;
}
```

### Key Components

1. **Constructor**: Accepts `DbContextOptions<ApplicationDbContext>` which contains the database provider and connection string configuration
2. **DbSet Properties**: Define the entity sets that map to database tables
3. **Base Class**: `IdentityDbContext` provides tables for user management

### Registration and Lifetime

The context is registered in the dependency injection container with a scoped lifetime in `Program.cs`. This means a new instance is created for each HTTP request, ensuring thread safety while optimizing resource usage.

### Configuration Options

While our current implementation uses the default configuration, you can customize the context behavior with additional options:

```csharp
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(connectionString)
           .UseQueryTrackingBehavior(QueryTrackingBehavior.NoTracking)
           .EnableSensitiveDataLogging(builder.Environment.IsDevelopment()));
```

For more information on database configuration, see the [Database Management Guide](/development_guide/database_management.md).

## CRUD Operations

Entity Framework Core simplifies Create, Read, Update, and Delete (CRUD) operations through its DbContext and DbSet APIs. Our `ToDoController` demonstrates these operations:

### Creating Entities

```csharp
// From ToDoController.cs - Create action
[HttpPost]
[ValidateAntiForgeryToken]
public IActionResult Create(ToDo.Models.ToDo todo)
{
    if (ModelState.IsValid)
    {
        _context.ToDos.Add(todo);
        _context.SaveChanges();
        return RedirectToAction(nameof(Index));
    }
    return View(todo);
}
```

The process involves:
1. Creating a new entity instance
2. Adding it to the appropriate DbSet
3. Calling `SaveChanges()` to persist the changes to the database

### Reading Entities

```csharp
// From ToDoController.cs - Index action
public IActionResult Index()
{
    return View(_context.ToDos.ToList());
}

// From ToDoController.cs - Details action
public IActionResult Details(int? id)
{
    if (id == null || _context.ToDos == null)
    {
        return RedirectToAction(\"Index\");
    }

    var toDos = _context.ToDos.FirstOrDefault(x => x.Id == id);
    if (toDos == null)
    {
        return NotFound();
    }

    return View(toDos);
}
```

Reading operations use LINQ methods like:
- `ToList()`: Retrieves all entities
- `FirstOrDefault()`: Retrieves a single entity based on a condition
- `Find()`: Retrieves an entity by primary key (not shown in the example)

### Updating Entities

```csharp
// From ToDoController.cs - Edit action
[HttpPost]
[ValidateAntiForgeryToken]
public IActionResult Edit(int? id, ToDo.Models.ToDo toDo)
{
    if (id != toDo.Id)
    {
        return NotFound();
    }

    if (ModelState.IsValid)
    {
        _context.ToDos.Update(toDo);
        _context.SaveChanges();
    }
    return RedirectToAction(\"Index\");
    }
    return View(toDo);
}
```

Updates involve:
1. Retrieving the entity or creating a detached entity with the same key
2. Modifying the entity properties
3. Calling `Update()` or marking the entity as modified
4. Calling `SaveChanges()` to persist changes

### Deleting Entities

```csharp
// From ToDoController.cs - DeleteConfirm action
[HttpPost, ActionName(\"Delete\")]
[ValidateAntiForgeryToken]
public IActionResult DeleteConfirm(int id)
{
    if (id == null || _context.ToDos == null)
    {
        return NotFound();
    }
    var toDos = _context.ToDos.FirstOrDefault(x => x.Id == id);
    if (toDos != null)
    {
        _context.ToDos.Remove(toDos);
        _context.SaveChanges();
    }

    return RedirectToAction(nameof(Index));
}
```

Deletion follows a similar pattern:
1. Retrieving the entity to delete
2. Removing it from the DbSet
3. Calling `SaveChanges()` to persist the deletion

### Best Practices

- Always validate user input before persisting changes
- Use `ModelState.IsValid` to check model validation
- Check for null entities before operations
- Consider using async methods for better scalability

## Querying Data

EF Core provides a powerful querying system built on LINQ (Language Integrated Query). This allows you to write type-safe queries that are translated to SQL at runtime.

### Basic Queries

```csharp
// Get all ToDo items
var allTodos = _context.ToDos.ToList();

// Get a specific ToDo by ID
var todo = _context.ToDos.Find(id);

// Get ToDos matching a condition
var completedTodos = _context.ToDos.Where(t => t.IsDone).ToList();
```

### Projection

Projection allows you to select specific properties rather than entire entities:

```csharp
// Select only the titles of completed ToDos
var completedTitles = _context.ToDos
    .Where(t => t.IsDone)
    .Select(t => t.Title)
    .ToList();
```

### Ordering

```csharp
// Order ToDos by date
var orderedTodos = _context.ToDos
    .OrderBy(t => t.Date)
    .ToList();

// Order by multiple criteria
var prioritizedTodos = _context.ToDos
    .OrderBy(t => t.IsDone)
    .ThenBy(t => t.Date)
    .ToList();
```

### Pagination

For better performance with large datasets, implement pagination:

```csharp
// Get page 2 with 10 items per page
var pageNumber = 2;
var pageSize = 10;
var pagedTodos = _context.ToDos
    .Skip((pageNumber - 1) * pageSize)
    .Take(pageSize)
    .ToList();
```

### Eager Loading

When working with related entities (not currently implemented in our ToDo model), use eager loading to avoid the N+1 query problem:

```csharp
// Example if ToDos had related Categories
var todosWithCategories = _context.ToDos
    .Include(t => t.Category)
    .ToList();
```

### Query Execution

It's important to understand when queries are executed:

- LINQ methods like `ToList()`, `FirstOrDefault()`, `Count()` execute the query immediately
- Without these methods, you're building a query that will execute when enumerated
- Use `IQueryable<T>` for building queries and `IEnumerable<T>` for working with results

### Performance Tips

- Use `AsNoTracking()` for read-only queries to improve performance
- Be specific with `Where` clauses to filter data at the database level
- Use `Select` to project only needed fields
- Consider adding indexes to frequently queried columns

For more information on data models and their relationships, see the [Data Models documentation](/architecture/data_models.md).

## Relationships

While our current ToDo model doesn't implement relationships, understanding how EF Core handles relationships is important for future development.

### Types of Relationships

1. **One-to-Many**: Most common relationship (e.g., one User has many ToDos)
2. **Many-to-Many**: Requires a join table (e.g., ToDos with multiple Tags)
3. **One-to-One**: Less common but useful for splitting large entities

### Defining Relationships

Relationships can be defined using either:

1. **Navigation Properties**: Define properties in your model classes
2. **Fluent API**: Configure relationships in `OnModelCreating`

#### Example: Adding User Relationship to ToDo

```csharp
// In ToDo.cs model
public class ToDo
{
    public int Id { get; set; }
    public string Title { get; set; } = String.Empty;
    public string Details { get; set; } = String.Empty;
    public DateTime Date { get; set; }
    public bool IsDone { get; set; }

    // Navigation property
    public string UserId { get; set; }
    public IdentityUser User { get; set; }
}

// In ApplicationDbContext.cs
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    base.OnModelCreating(modelBuilder);

    modelBuilder.Entity<ToDo>()
        .HasOne(t => t.User)
        .WithMany()
        .HasForeignKey(t => t.UserId)
        .IsRequired();
}
```

### Loading Related Data

EF Core provides three ways to load related data:

1. **Eager Loading**: Load related data in the same query using `Include()`
2. **Explicit Loading**: Load related data later using `Entry().Collection().Load()`
3. **Lazy Loading**: Automatically load related data when the navigation property is accessed (requires additional configuration)

### Cascade Delete

By default, EF Core configures cascade delete for required relationships. You can customize this behavior:

```csharp
modelBuilder.Entity<ToDo>()
    .HasOne(t => t.User)
    .WithMany()
    .HasForeignKey(t => t.UserId)
    .OnDelete(DeleteBehavior.Restrict);
```

## Migrations Workflow

Migrations are a crucial feature of EF Core that allow you to evolve your database schema as your model changes. Our application uses migrations to create and update the database schema.

### Migration Commands

Using the Package Manager Console:

```
Add-Migration MigrationName
Update-Database
```

Using the .NET CLI:

```
dotnet ef migrations add MigrationName
dotnet ef database update
```

### Migration Process

1. **Create Initial Migration**: After defining your models, create the initial migration
2. **Apply Migration**: Update the database to create the schema
3. **Model Changes**: Modify your entity classes as requirements change
4. **Create New Migration**: Generate a migration for the changes
5. **Review Migration**: Check the generated code for correctness
6. **Apply Updated Migration**: Update the database with the new schema

### Migration Files

Each migration creates two files:
- `XXXXXXXXXXXXXXXX_MigrationName.cs`: Contains `Up()` and `Down()` methods
- `XXXXXXXXXXXXXXXX_MigrationName.Designer.cs`: Contains metadata about the migration

### Snapshot File

The `ApplicationDbContextModelSnapshot.cs` file maintains a representation of the current model state:

```csharp
// From ApplicationDbContextModelSnapshot.cs
modelBuilder.Entity(\"ToDo.Models.ToDo\", b =>
{
    b.Property<int>(\"Id\")
        .ValueGeneratedOnAdd()
        .HasColumnType(\"int\");
    b.Property<DateTime>(\"Date\")
        .HasColumnType(\"datetime2\");
    b.Property<string>(\"Details\")
        .IsRequired()
        .HasColumnType(\"nvarchar(max)\");
    b.Property<bool>(\"IsDone\")
        .HasColumnType(\"bit\");
    b.Property<string>(\"Title\")
        .IsRequired()
        .HasColumnType(\"nvarchar(max)\");
    b.HasKey(\"Id\");
    b.ToTable(\"ToDos\");
});
```

### Best Practices

- Create small, focused migrations rather than large ones
- Test migrations thoroughly before applying to production
- Use meaningful migration names that describe the changes
- Consider using a separate migration for each feature
- Back up your database before applying migrations in production

For more information on database migrations, see the [Database Migration Guide](/deployment/database_migration.md).

## Advanced Features

EF Core offers several advanced features that can enhance your data access layer.

### Raw SQL Queries

When LINQ doesn't provide the functionality you need, you can execute raw SQL:

```csharp
// Execute a raw SQL query
var todos = _context.ToDos
    .FromSqlRaw(\"SELECT * FROM ToDos WHERE Date > {0}\", DateTime.Today)
    .ToList();

// Execute a non-query command
_context.Database.ExecuteSqlRaw(\"UPDATE ToDos SET IsDone = 1 WHERE Date < {0}\", DateTime.Today);
```

### Global Query Filters

Define filters that automatically apply to all queries:

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    base.OnModelCreating(modelBuilder);

    // Filter to only show current user's ToDos
    modelBuilder.Entity<ToDo>().HasQueryFilter(t => t.UserId == _currentUserId);
}
```

### Value Conversions

Convert between property types and database column types:

```csharp
// Store enum as string
modelBuilder.Entity<ToDo>()
    .Property(t => t.Priority)
    .HasConversion<string>();
```

### Owned Entity Types

Use owned entities to split large entities into smaller components:

```csharp
modelBuilder.Entity<ToDo>().OwnsOne(t => t.Reminder, r =>
{
    r.Property(p => p.AlertTime).HasColumnName(\"ReminderTime\");
    r.Property(p => p.AlertType).HasColumnName(\"ReminderType\");
});
```

### Concurrency Tokens

Handle concurrency conflicts with tokens:

```csharp
modelBuilder.Entity<ToDo>()
    .Property(t => t.RowVersion)
    .IsRowVersion();
```

### Compiled Queries

Improve performance by compiling frequently used queries:

```csharp
private static readonly Func<ApplicationDbContext, int, Task<ToDo>> _getTodoById =
    EF.CompileAsyncQuery((ApplicationDbContext context, int id) =>
        context.ToDos.FirstOrDefault(t => t.Id == id));

// Usage
var todo = await _getTodoById(_context, id);
```

## Performance Considerations

Optimizing EF Core performance is crucial for application responsiveness and scalability.

### N+1 Query Problem

The N+1 query problem occurs when you load a collection of entities and then access a related entity for each one, causing additional database queries:

```csharp
// Bad: Causes N+1 queries
var todos = _context.ToDos.ToList();
foreach (var todo in todos)
{
    // This causes an additional query for each todo
    var user = todo.User;
}

// Good: Uses eager loading to avoid N+1 queries
var todos = _context.ToDos.Include(t => t.User).ToList();
```

### Tracking vs. No-Tracking

Entity tracking is useful for updates but adds overhead:

```csharp
// With tracking (default) - use for entities you'll modify
var todoToUpdate = _context.ToDos.FirstOrDefault(t => t.Id == id);

// Without tracking - use for read-only scenarios
var todoReadOnly = _context.ToDos.AsNoTracking().FirstOrDefault(t => t.Id == id);
```

### Batching Updates

EF Core sends individual commands by default. Consider batching for bulk operations:

```csharp
// Add multiple entities in one SaveChanges call
_context.ToDos.Add(todo1);
_context.ToDos.Add(todo2);
_context.ToDos.Add(todo3);
_context.SaveChanges(); // One database round-trip
```

### Pagination

Always implement pagination for large result sets:

```csharp
var pagedTodos = _context.ToDos
    .OrderBy(t => t.Date)
    .Skip((pageNumber - 1) * pageSize)
    .Take(pageSize)
    .ToList();
```

### Projection

Select only the properties you need:

```csharp
// Instead of loading full entities
var todoSummaries = _context.ToDos
    .Select(t => new TodoSummary
    {
        Id = t.Id,
        Title = t.Title,
        IsDone = t.IsDone
    })
    .ToList();
```

### Indexing

Add indexes to frequently queried columns in your migrations:

```csharp
protected override void Up(MigrationBuilder migrationBuilder)
{
    // Other migration code...

    migrationBuilder.CreateIndex(
        name: \"IX_ToDos_Date\",
        table: \"ToDos\",
        column: \"Date\");
}
```

### Async Methods

Use async methods for better scalability:

```csharp
// Instead of:
var todos = _context.ToDos.ToList();

// Use:
var todos = await _context.ToDos.ToListAsync();
```

### Monitoring and Logging

Enable logging to identify performance issues:

```csharp
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(connectionString)
           .EnableSensitiveDataLogging()
           .LogTo(Console.WriteLine, LogLevel.Information));
```

For more information on MVC development patterns that work with EF Core, see the [MVC Development Guide](/development_guide/mvc_development.md).

---

By following these guidelines and best practices, you'll be able to effectively use Entity Framework Core in the ToDo application, ensuring efficient data access, maintainable code, and optimal performance."
      tech_stack "Based on the provided `.csproj` file, I'll create a comprehensive technical stack description for this project.

## Backend
The backend is built using **ASP.NET Core** targeting **.NET 8.0**. This is a modern, cross-platform framework for building web applications and services. The project appears to be a web application with built-in authentication and authorization capabilities through ASP.NET Core Identity.

## Database
The application uses **Microsoft SQL Server** as its database system, as indicated by the `Microsoft.EntityFrameworkCore.SqlServer` package. **Entity Framework Core** serves as the ORM (Object-Relational Mapper), providing database access and management capabilities. The project also includes EF Core Tools for migrations and database management tasks.

## Key Libraries & Dependencies
- **ASP.NET Core Identity**: Provides user authentication, authorization, and account management functionality.
- **Entity Framework Core**: ORM for database operations with SQL Server integration.
- **ASP.NET Core Diagnostics for EF Core**: Provides middleware for Entity Framework Core error pages.
- **Visual Studio Web Code Generation**: Tools for scaffolding controllers, views, and other components.

## Other Notable Technologies
- The project uses **User Secrets** for secure configuration management in development environments, as indicated by the `UserSecretsId` property.
- **Nullable reference types** are enabled, indicating a focus on preventing null reference exceptions.
- **Implicit usings** are enabled, which simplifies code by automatically including common namespaces.

## Technology Versions

| Technology | Version |
|------------|---------|
| .NET | 8.0 |
| ASP.NET Core | 8.0 |
| Entity Framework Core | 7.0.10 |
| ASP.NET Core Identity | 7.0.10 |
| ASP.NET Core Identity UI | 7.0.10 |
| EF Core SQL Server Provider | 7.0.10 |
| VS Web Code Generation | 8.0.0-rc.1.23461.3 |"
      relevant_source_file_content "﻿using System.ComponentModel.DataAnnotations;

namespace ToDo.Models
{
    public class ToDo
    {

        [Key]
        public int Id { get; set; }

        [Required(ErrorMessage = \"Title is required\")]
        public string Title { get; set; } = String.Empty;

        [DataType(DataType.MultilineText)]
        public string Details { get; set; } = String.Empty;

        [DataType(DataType.DateTime)]
        public DateTime Date { get; set; }

        [Display(Name = \"Is Done\")]
        public bool IsDone { get; set; }
    }
}
"#
    }
    }
}
