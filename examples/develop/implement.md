# Implement Feature

Fully implement a feature by executing all tasks in the task list, writing production code and documentation in the target codebase directories.

## Usage

```
/implement key: [key] type: [type]
```

**Examples:**
```
/implement key: 1075-spring-filterservice-load type: api-endpoints
```

```
/implement key: 2105-infrastructure-company-company-maintenance type: ui-features
```

## Input

The command receives an inventory item JSON payload:

```json
{
  "key": "1075-spring-filterservice-load",
  "name": null,
  "location": "./legacy/northwest-passage/passage-java/src-common/com/williams/gridServices/services/FilterService.java, FilterService.load() method (line 93)",
  "type": "api-endpoints",
  "notes": [
    "Spring REST reflection endpoint: POST /service/gridServices",
    "Bean ID: filterService",
    "Client specifies methodName in POST body (JSON-RPC style)"
  ]
}
```

Use `type` and `key` to locate the entry point directory:
```
./docs/entry-points/{type}/{key}/
```

## CRITICAL: Autonomous Execution

**This command MUST execute autonomously without asking for user input.**

**DO NOT:**
- Present multiple options and ask the user to choose
- Ask for approval before proceeding with implementation
- Suggest "phased approaches" or "iterative implementation" and wait for user input
- Stop and ask "which approach would you prefer?"
- Present recommendations and wait for user confirmation

**DO:**
- Make implementation decisions autonomously based on the implementation plan
- If the implementation is large, use **Task subagents** to parallelize work
- Proceed directly with implementation after reading the required documents
- Complete all tasks in the task list without stopping for approval

### Using Task Subagents for Large Implementations

When the implementation involves many components (multiple DTOs, services, repositories, controllers), break the work into parallel Task subagent invocations:

```
Example: Large backend implementation

1. Read all input documents (do this yourself in main context)
2. Launch parallel Task subagents:
   - Task 1: "Implement all DTOs in ./passage-api/src/modules/[feature]/dto/"
   - Task 2: "Implement all entities in ./passage-api/src/modules/[feature]/entities/"
3. Wait for completion, then launch next wave:
   - Task 3: "Implement repositories"
   - Task 4: "Implement services"
4. Final wave:
   - Task 5: "Implement controllers"
   - Task 6: "Configure module"
```

**Task subagent prompts should include:**
- The specific files to create
- The technical specifications from the plan
- Reference to existing patterns in the codebase
- Clear success criteria

### Developer Agents

Use specialized developer agents for domain-specific implementation:

| Agent | Color | Use For |
|-------|-------|---------|
| `passage-api-developer` | magenta | Controllers, services, repositories, entities, DTOs |
| `passage-ui-developer` | teal | Components, services, models, Kendo configs |
| `passage-db-developer` | lime | DDL scripts, migrations, indexes |
| `batch-developer` | gold | Batch jobs, steps, readers/processors/writers |
| `trigger-developer` | coral | Trigger replacements, JPA auditing, validation services |
| `pattern-registry-developer` | silver | Register new patterns discovered during implementation |

### Parallel Execution Strategy

**CRITICAL: Maximize parallelization by launching sub-agents in a SINGLE message.**

When multiple tasks are independent, launch all their sub-agents together:

```python
# CORRECT - Launch independent tasks in ONE message (parallel execution):
Task(subagent_type="passage-api-developer", prompt="Implement request DTOs...")
Task(subagent_type="passage-api-developer", prompt="Implement response DTOs...")
Task(subagent_type="passage-api-developer", prompt="Implement repository interfaces...")

# After ALL complete, launch dependent tasks:
Task(subagent_type="passage-api-developer", prompt="Implement services using the DTOs and repos...")

# INCORRECT - Sequential when could be parallel:
Task(subagent_type="passage-api-developer", prompt="Implement request DTOs...")
# Wait...
Task(subagent_type="passage-api-developer", prompt="Implement response DTOs...")
# Wait...
```

**Parallelization rules:**
1. **Independent tasks** → launch in single message (parallel execution)
2. **Dependent tasks** → wait for blockers to complete first
3. **Consult `task-list.md` Dependency Matrix** for guidance on what can parallelize

**Standard API implementation waves:**

| Wave | Parallel Tasks | Sub-agents |
|------|---------------|------------|
| 1 | Request DTOs, Response DTOs, Entity definitions | 3 parallel |
| 2 | Repository interfaces, Custom queries | 2 parallel |
| 3 | Service implementation | 1 parallel |
| 4 | Controller implementation | 1 parallel |

### Claude Task Progress Tracking

Use Claude's `TaskCreate`/`TaskUpdate` tools to track phase-level progress:

**Before starting each phase/wave:**
```python
TaskUpdate(taskId="phase-2-api-id", status="in_progress")
```

**After completing each phase/wave:**
```python
TaskUpdate(taskId="phase-2-api-id", status="completed")
# Check what's now unblocked
TaskList()
```

**Example tracking flow:**
```
# Start Wave 1 (DTOs)
TaskUpdate(taskId="dto-phase-id", status="in_progress")

# Launch parallel sub-agents for DTOs
Task(subagent_type="passage-api-developer", prompt="Request DTOs...")
Task(subagent_type="passage-api-developer", prompt="Response DTOs...")

# After all complete:
TaskUpdate(taskId="dto-phase-id", status="completed")

# Start Wave 2 (Repositories) - now unblocked
TaskUpdate(taskId="repo-phase-id", status="in_progress")
# ... continue pattern
```

**Benefits:**
- Visual progress tracking for user
- Clear indication of what's blocked vs. ready
- Helps with retry/resume scenarios

### Decision-Making Authority

You have full authority to make implementation decisions:
- Choose between equivalent implementation approaches
- Determine optimal order of operations
- Select appropriate patterns from the codebase

If something in the implementation plan is unclear or seems wrong, make your best judgment and document your decision in the code comments. Do NOT stop to ask the user.

## What This Command Does

This command performs the complete implementation of a feature by:

1. **Reading** the implementation plan and task list
2. **Understanding** target architecture patterns and existing codebase structure
3. **Implementing** all required code in the target directories:
   - `./passage-api/` - Backend implementation (NestJS/TypeScript)
   - `./passage-ui/` - Frontend implementation (React/TypeScript)
4. **Updating** documentation (code comments, API docs, architecture docs)
5. **Tracking** progress by updating task list checkboxes
6. **Verifying** implementation compiles and builds successfully

**CRITICAL**: This command writes actual production code, not just plans or outlines.

## Target Directories

### Backend: ./passage-api/

NestJS TypeScript application structure:
```
./passage-api/
├── src/
│   ├── modules/              # Feature modules
│   │   ├── [feature]/
│   │   │   ├── controllers/  # REST controllers
│   │   │   ├── services/     # Business logic services
│   │   │   ├── repositories/ # Data access layer
│   │   │   ├── entities/     # Domain entities
│   │   │   ├── dto/          # Data Transfer Objects
│   │   │   ├── validators/   # Custom validators
│   │   │   ├── [feature].module.ts
│   │   │   └── index.ts
│   ├── common/               # Shared code
│   │   ├── decorators/
│   │   ├── filters/
│   │   ├── guards/
│   │   ├── interceptors/
│   │   └── pipes/
│   ├── config/               # Configuration
│   └── database/             # Database migrations
└── test/                     # Test files
    ├── unit/
    ├── integration/
    └── e2e/
```

### Frontend: ./passage-ui/

React TypeScript application structure:
```
./passage-ui/
├── src/
│   ├── features/             # Feature-based modules
│   │   ├── [feature]/
│   │   │   ├── components/   # React components
│   │   │   ├── hooks/        # Custom hooks
│   │   │   ├── services/     # API client services
│   │   │   ├── types/        # TypeScript types
│   │   │   ├── utils/        # Utilities
│   │   │   └── index.ts
│   ├── shared/               # Shared code
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── utils/
│   ├── api/                  # API client configuration
│   ├── store/                # State management
│   └── routes/               # Routing configuration
└── test/                     # Test files
```

## Input Structure

The entry point directory at `./docs/entry-points/{type}/{key}/` contains:

```
{entry-point-directory}/
├── metadata.json                    # Entry point metadata
├── implementation-plan.md                # Technical implementation plan (INPUT)
├── task-list.md                     # Hierarchical task list (INPUT)
├── api.openapi.json                 # OpenAPI spec (if applicable)
├── functional-spec.md               # Functional specification (reference)
└── code/                            # Legacy code reference
```

**Required files**:
- `implementation-plan.md` - Contains all technical specifications
- `task-list.md` - Contains ordered list of tasks to execute

## Implementation Process

### Phase 0: Initial Setup and Understanding

**CRITICAL**: Complete this phase before writing any code.

1. **Read all input documents**:
   - [ ] Read `task-list.md` completely - understand all tasks
   - [ ] Read `implementation-plan.md` completely - understand architecture
   - [ ] Read `functional-spec.md` - understand requirements
   - [ ] Read `api.openapi.json` (if exists) - understand API contracts

2. **Read target architecture documentation**:
   - [ ] Consult `./docs/target-architecture/index.md` to determine which documents are relevant for your implementation task. YOU MUST READ THEM.

3. **Understand existing codebase patterns**:
   - [ ] Explore `./passage-api/src/modules/` to understand module structure
   - [ ] Find similar existing features to use as reference
   - [ ] Understand dependency injection patterns
   - [ ] Understand error handling patterns
   - [ ] Understand validation patterns
   - [ ] (If UI) Explore `./passage-ui/src/features/` to understand component patterns
   - [ ] Check if any stored procedures in `database-dependencies.json` have already been converted (search `passage-api/src` for the SP name or derived service class name)

4. **Create comprehensive TodoWrite list**:
   - [ ] Create todos matching all checkboxed items from task-list.md
   - [ ] Organize todos in implementation order
   - [ ] Mark first todo as in_progress

### Phase 1: Backend Foundation (API Layer)

**For API endpoints or backend features:**

#### 1.0. Stored Procedure Conversion (when applicable)

**Before building the service/controller layers**, convert any stored procedures that haven't already been converted by another endpoint. Check the implementation plan's `## Stored Procedure Conversion Strategy` section.

1. **Read the conversion guide**: `docs/target-architecture/patterns/api-patterns/stored-procedure-conversion.v9.md`
2. **Follow the conversion pattern** identified in the implementation plan for each SP
3. **Reference worked examples**: `docs/conversions/` contains real SP conversion examples
4. **Create shared service classes**: Convert SP logic into a shared service class (not inlined into the endpoint service) so other endpoints can reuse it
5. **Write unit tests** for the converted SP logic before proceeding to service layer
   - **Required**: Dedicated mapper unit tests validating DTO-to-entity field mapping (especially type conversions like `Boolean` → `"Y"/"N"`, nullable fields, date conversions, default values)
   - **Required**: Unit tests covering all conditional branches in the SP logic
   - **Recommended**: At least one integration test with real database validating JPA entity-to-schema mapping, audit field behavior, and constraint handling
6. **For already-converted SPs**: Verify the existing service class covers this endpoint's usage. Add missing methods/overloads if needed. Import and wire into this endpoint's service.
7. **Create conversion doc**: Create `docs/conversions/{sp_name}_conversion.md` following the established template (see existing docs in `docs/conversions/` for format). Must include:
   - Original SP file path, line count, parameter list, and business purpose
   - Complexity tier and scoring breakdown (from v9 rubric)
   - Modern implementation: architecture, files created/modified, key design decisions
   - Key improvements over legacy
   - Testing summary and file references
8. **Add code traceability comments**: Add class-level JavaDoc to the primary service class:
   ```java
   /**
    * Service for [description]. Replaces stored procedure: {sp_name}.sp
    *
    * <p>Migrated from: dbo.{sp_name}
    * Source: legacy/database/PROCS/{folder}/{sp_name}.sp
    */
   ```
   If the conversion spans multiple service classes (e.g., a dispatch service + operation service), add the comment to the top-level service and add `@see PrimaryService` to subordinate classes.

**SP conversion completes before DTOs/Service/Controller work begins.**

#### 1.1. DTOs and Contracts

For each Request/Response DTO in implementation plan:

```typescript
// ./passage-api/src/modules/[feature]/dto/[name].dto.ts

import { IsNotEmpty, IsOptional, IsString, IsNumber } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

/**
 * [DTO description from implementation plan]
 */
export class [Name]Dto {
  /**
   * [Field description from implementation plan]
   * @example [example value]
   */
  @ApiProperty({
    description: '[field description]',
    example: '[example]'
  })
  @IsNotEmpty()
  @IsString()
  fieldName: string;

  /**
   * [Optional field description]
   */
  @ApiPropertyOptional({
    description: '[field description]',
    example: '[example]'
  })
  @IsOptional()
  @IsNumber()
  optionalField?: number;
}
```

**After creating each DTO**:
- [ ] Mark DTO creation task as complete in task-list.md
- [ ] Update todo as completed
- [ ] Move to next task

#### 1.2. Domain Entities

For each entity in implementation plan:

```typescript
// ./passage-api/src/modules/[feature]/entities/[name].entity.ts

import { Entity, Column, PrimaryGeneratedColumn, ManyToOne, JoinColumn } from 'typeorm';

/**
 * [Entity description from implementation plan]
 *
 * Database table: [TABLE_NAME]
 */
@Entity('[TABLE_NAME]')
export class [Name]Entity {
  /**
   * [Primary key description]
   */
  @PrimaryGeneratedColumn()
  id: number;

  /**
   * [Field description from implementation plan]
   * Maps to column: [COLUMN_NAME]
   */
  @Column({ name: '[COLUMN_NAME]', type: 'varchar', length: 100 })
  fieldName: string;

  /**
   * [Relationship description]
   */
  @ManyToOne(() => RelatedEntity)
  @JoinColumn({ name: '[FK_COLUMN_NAME]' })
  relatedEntity: RelatedEntity;
}
```

**After creating each entity**:
- [ ] Mark entity creation task as complete in task-list.md
- [ ] Update todo as completed

#### 1.3. Repository Layer

For each repository in implementation plan:

```typescript
// ./passage-api/src/modules/[feature]/repositories/[name].repository.ts

import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { [Name]Entity } from '../entities/[name].entity';

/**
 * [Repository description from implementation plan]
 */
@Injectable()
export class [Name]Repository {
  constructor(
    @InjectRepository([Name]Entity)
    private readonly repository: Repository<[Name]Entity>,
  ) {}

  /**
   * [Method description from implementation plan]
   *
   * Query: SELECT ... FROM [TABLE] WHERE ...
   */
  async findById(id: number): Promise<[Name]Entity | null> {
    return this.repository.findOne({ where: { id } });
  }

  /**
   * [Method description from implementation plan]
   */
  async findByCondition(params: SearchParams): Promise<[Name]Entity[]> {
    const queryBuilder = this.repository.createQueryBuilder('[alias]');

    // Build query according to implementation plan specifications
    if (params.filter) {
      queryBuilder.where('[condition]', { param: params.filter });
    }

    return queryBuilder.getMany();
  }

  /**
   * [Method description from implementation plan]
   */
  async save(entity: [Name]Entity): Promise<[Name]Entity> {
    return this.repository.save(entity);
  }

  /**
   * [Method description from implementation plan]
   */
  async delete(id: number): Promise<boolean> {
    const result = await this.repository.delete(id);
    return result.affected > 0;
  }
}
```

**After creating each repository**:
- [ ] Mark repository creation task as complete in task-list.md

#### 1.5. Service Layer

For each service in implementation plan:

```typescript
// ./passage-api/src/modules/[feature]/services/[name].service.ts

import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { [Name]Repository } from '../repositories/[name].repository';
import { [Request]Dto } from '../dto/[request].dto';
import { [Response]Dto } from '../dto/[response].dto';

/**
 * [Service description from implementation plan]
 */
@Injectable()
export class [Name]Service {
  constructor(
    private readonly repository: [Name]Repository,
    // Additional dependencies from implementation plan
  ) {}

  /**
   * [Method description from implementation plan]
   *
   * Business Rules Applied:
   * - [Rule 1 from implementation plan]
   * - [Rule 2 from implementation plan]
   *
   * @param input - [Parameter description]
   * @returns [Return description]
   * @throws NotFoundException when [condition]
   * @throws BadRequestException when [condition]
   */
  async methodName(input: [Request]Dto): Promise<[Response]Dto> {
    // Implementation based on implementation plan notes:

    // 1. Validate input
    this.validateInput(input);

    // 2. Fetch related data
    const entity = await this.repository.findById(input.id);
    if (!entity) {
      throw new NotFoundException(`[Entity] with id ${input.id} not found`);
    }

    // 3. Apply business rule: [rule description from implementation plan]
    if (/* business rule condition */) {
      throw new BadRequestException('[Business rule violation message]');
    }

    // 4. Persist changes
    const result = await this.repository.save(/* transformed data */);

    // 5. Return mapped response
    return this.mapToDto(result);
  }

  /**
   * Validates input according to business rules
   */
  private validateInput(input: [Request]Dto): void {
    // Validation logic from implementation plan
  }

  /**
   * Maps entity to response DTO
   */
  private mapToDto(entity: [Name]Entity): [Response]Dto {
    // Mapping logic
    return {
      // Map fields according to implementation plan
    };
  }
}
```

**After creating each service**:
- [ ] Mark service creation task as complete in task-list.md

#### 1.7. Controller Layer

**CRITICAL CONSTRAINT — Zero Business Logic in Controllers**

Controllers must contain ZERO business logic. They accept payloads, call services, and return responses. Specifically:

- **Allowed in controllers:** `@Valid` validation, `@RequestParam`/`@PathVariable` binding, OpenAPI annotations, Spring Security annotations (`@PreAuthorize`, `@Secured`), logging, delegating to a single service method, constructing `ResponseEntity`
- **NOT allowed in controllers:** Date parsing, conditional routing, DTO assembly from multiple sources, format conversion, orchestration between services, data transformation, business rule checks

If the implementation plan places business logic in the controller, move it to the appropriate service before implementing. Create a new service method if needed.

For each API endpoint in implementation plan:

```typescript
// ./passage-api/src/modules/[feature]/controllers/[name].controller.ts

import {
  Controller,
  Post,
  Get,
  Put,
  Delete,
  Body,
  Param,
  Query,
  UseGuards,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBearerAuth,
} from '@nestjs/swagger';
import { [Name]Service } from '../services/[name].service';
import { [Request]Dto } from '../dto/[request].dto';
import { [Response]Dto } from '../dto/[response].dto';
import { JwtAuthGuard } from '@/common/guards/jwt-auth.guard';
import { PermissionsGuard } from '@/common/guards/permissions.guard';
import { RequirePermissions } from '@/common/decorators/permissions.decorator';

/**
 * [Controller description from implementation plan]
 */
@ApiTags('[Feature]')
@Controller('[feature-path]')
@UseGuards(JwtAuthGuard, PermissionsGuard)
@ApiBearerAuth()
export class [Name]Controller {
  constructor(private readonly service: [Name]Service) {}

  /**
   * [Endpoint description from implementation plan]
   */
  @Post()
  @ApiOperation({ summary: '[Operation summary from OpenAPI]' })
  @ApiResponse({
    status: 201,
    description: 'Successfully created',
    type: [Response]Dto,
  })
  @ApiResponse({
    status: 400,
    description: 'Validation error',
  })
  @ApiResponse({
    status: 403,
    description: 'Insufficient permissions',
  })
  @RequirePermissions('[PERMISSION_CODE]')
  @HttpCode(HttpStatus.CREATED)
  async create(@Body() request: [Request]Dto): Promise<[Response]Dto> {
    return this.service.create(request);
  }

  /**
   * [Endpoint description]
   */
  @Get(':id')
  @ApiOperation({ summary: '[Operation summary]' })
  @ApiResponse({
    status: 200,
    description: 'Successfully retrieved',
    type: [Response]Dto,
  })
  @ApiResponse({
    status: 404,
    description: 'Not found',
  })
  @RequirePermissions('[PERMISSION_CODE]')
  async findById(@Param('id') id: number): Promise<[Response]Dto> {
    return this.service.findById(id);
  }

  // Additional endpoints according to implementation plan
}
```

**After creating each controller**:
- [ ] Mark controller creation task as complete in task-list.md

#### 1.9. Module Configuration

Create or update the feature module:

```typescript
// ./passage-api/src/modules/[feature]/[feature].module.ts

import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { [Name]Controller } from './controllers/[name].controller';
import { [Name]Service } from './services/[name].service';
import { [Name]Repository } from './repositories/[name].repository';
import { [Name]Entity } from './entities/[name].entity';

/**
 * [Feature] module
 *
 * Provides: [description from implementation plan]
 */
@Module({
  imports: [
    TypeOrmModule.forFeature([[Name]Entity]),
  ],
  controllers: [[Name]Controller],
  providers: [
    [Name]Service,
    [Name]Repository,
  ],
  exports: [[Name]Service],
})
export class [Feature]Module {}
```

Register in app module:

```typescript
// ./passage-api/src/app.module.ts

import { [Feature]Module } from './modules/[feature]/[feature].module';

@Module({
  imports: [
    // ... existing imports
    [Feature]Module,
  ],
})
export class AppModule {}
```

**After module configuration**:
- [ ] Mark module creation task as complete in task-list.md

### Phase 2: Database Changes

**If implementation plan includes database changes:**

#### 2.1. Create Migration Scripts

```typescript
// ./passage-api/src/database/migrations/[timestamp]-[description].ts

import { MigrationInterface, QueryRunner, Table, TableForeignKey, TableIndex } from 'typeorm';

/**
 * [Migration description from implementation plan]
 */
export class [MigrationName][Timestamp] implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Create new tables (from implementation plan)
    await queryRunner.createTable(
      new Table({
        name: '[TABLE_NAME]',
        columns: [
          {
            name: 'id',
            type: 'int',
            isPrimary: true,
            isGenerated: true,
            generationStrategy: 'increment',
          },
          {
            name: '[column_name]',
            type: 'varchar',
            length: '100',
            isNullable: false,
          },
          // Additional columns from implementation plan
        ],
      }),
      true,
    );

    // Create foreign keys (from implementation plan)
    await queryRunner.createForeignKey(
      '[TABLE_NAME]',
      new TableForeignKey({
        columnNames: ['[fk_column]'],
        referencedTableName: '[referenced_table]',
        referencedColumnNames: ['id'],
        onDelete: 'CASCADE',
      }),
    );

    // Create indexes (from implementation plan)
    await queryRunner.createIndex(
      '[TABLE_NAME]',
      new TableIndex({
        name: 'IDX_[TABLE]_[COLUMNS]',
        columnNames: ['[column1]', '[column2]'],
      }),
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    // Rollback operations (from implementation plan)
    await queryRunner.dropTable('[TABLE_NAME]');
  }
}
```

**After creating migration**:
- [ ] Run migration: `npm run migration:run`
- [ ] Verify database changes
- [ ] Test rollback: `npm run migration:revert`
- [ ] Re-run migration
- [ ] Mark migration task as complete in task-list.md

### Phase 3: Frontend Implementation (UI Features)

**For UI features:**

#### 3.1. TypeScript Types

```typescript
// ./passage-ui/src/features/[feature]/types/[name].types.ts

/**
 * [Type description from implementation plan]
 */
export interface [Name]Request {
  /**
   * [Field description]
   */
  fieldName: string;

  /**
   * [Optional field description]
   */
  optionalField?: number;
}

/**
 * [Type description from implementation plan]
 */
export interface [Name]Response {
  /**
   * [Field description]
   */
  id: number;

  /**
   * [Field description]
   */
  data: {
    nestedField: string;
  };
}

/**
 * Component props interface
 */
export interface [Component]Props {
  /**
   * [Prop description]
   */
  propName: string;

  /**
   * [Callback description]
   */
  onAction?: (value: any) => void;
}
```

#### 3.2. API Client Services

```typescript
// ./passage-ui/src/features/[feature]/services/[name].service.ts

import axios from '@/api/axios-instance';
import { [Request]Type, [Response]Type } from '../types/[name].types';

/**
 * [Service description from implementation plan]
 */
export class [Name]Service {
  private readonly basePath = '/api/v1/[resource]';

  /**
   * [Method description from implementation plan]
   */
  async create(request: [Request]Type): Promise<[Response]Type> {
    const response = await axios.post<[Response]Type>(
      this.basePath,
      request
    );
    return response.data;
  }

  /**
   * [Method description]
   */
  async findById(id: number): Promise<[Response]Type> {
    const response = await axios.get<[Response]Type>(
      `${this.basePath}/${id}`
    );
    return response.data;
  }

  /**
   * [Method description]
   */
  async update(id: number, request: [Request]Type): Promise<[Response]Type> {
    const response = await axios.put<[Response]Type>(
      `${this.basePath}/${id}`,
      request
    );
    return response.data;
  }

  /**
   * [Method description]
   */
  async delete(id: number): Promise<void> {
    await axios.delete(`${this.basePath}/${id}`);
  }
}

// Export singleton instance
export const [name]Service = new [Name]Service();
```

#### 3.3. Custom Hooks

```typescript
// ./passage-ui/src/features/[feature]/hooks/use-[name].ts

import { useState, useEffect, useCallback } from 'react';
import { [name]Service } from '../services/[name].service';
import { [Response]Type } from '../types/[name].types';

/**
 * [Hook description from implementation plan]
 */
export function use[Name](id?: number) {
  const [data, setData] = useState<[Response]Type | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  /**
   * Fetch data
   */
  const fetchData = useCallback(async () => {
    if (!id) return;

    setLoading(true);
    setError(null);

    try {
      const result = await [name]Service.findById(id);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [id]);

  /**
   * Create new resource
   */
  const create = useCallback(async (request: [Request]Type) => {
    setLoading(true);
    setError(null);

    try {
      const result = await [name]Service.create(request);
      setData(result);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Update resource
   */
  const update = useCallback(async (id: number, request: [Request]Type) => {
    setLoading(true);
    setError(null);

    try {
      const result = await [name]Service.update(id, request);
      setData(result);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    create,
    update,
  };
}
```

#### 3.4. React Components

```typescript
// ./passage-ui/src/features/[feature]/components/[Name].tsx

import React, { useState } from 'react';
import { [Component]Props } from '../types/[name].types';
import { use[Name] } from '../hooks/use-[name]';

/**
 * [Component description from implementation plan]
 */
export const [Name]Component: React.FC<[Component]Props> = ({
  propName,
  onAction,
}) => {
  const { data, loading, error, create, update } = use[Name]();
  const [formData, setFormData] = useState({
    // Form state
  });

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await create(formData);
      onAction?.('success');
    } catch (err) {
      // Error handling
      console.error('Failed to submit:', err);
    }
  };

  /**
   * Handle form field changes
   */
  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <div className="[feature]-[component]">
      <form onSubmit={handleSubmit}>
        {/* Form fields according to implementation plan */}
        <input
          type="text"
          value={formData.fieldName}
          onChange={(e) => handleChange('fieldName', e.target.value)}
          placeholder="[Field label]"
        />

        <button type="submit">
          Submit
        </button>
      </form>
    </div>
  );
};
```

### Phase 4: Documentation

#### 5.1. Code Documentation

**For all created files**:
- [ ] Add JSDoc/TSDoc comments to all public classes
- [ ] Add method-level documentation with examples
- [ ] Document complex logic with inline comments
- [ ] Add @param, @returns, @throws tags

#### 5.2. API Documentation

If OpenAPI spec was created, generate documentation:

```bash
# Generate API documentation
npm run api-docs:generate
```

Update API documentation with:
- [ ] Usage examples for each endpoint
- [ ] Authentication requirements
- [ ] Rate limiting information
- [ ] Common error scenarios

#### 5.3. Architecture Documentation

Update architecture documents:

```markdown
// ./docs/architecture/modules/[feature].md

# [Feature] Module

## Overview
[Description of what this module does]

## Architecture
[Component diagram showing module structure]

## Components

### Controllers
- `[Name]Controller` - [Description]

### Services
- `[Name]Service` - [Description]

### Repositories
- `[Name]Repository` - [Description]

### Entities
- `[Name]Entity` - [Description]

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/[resource] | [Description] |

## Database Schema

### Tables
- `[TABLE_NAME]` - [Purpose]

## Dependencies
- [Module dependencies]

## Notes
- [Any implementation notes]
```

**After documentation updates**:
- [ ] Mark documentation tasks as complete in task-list.md

### Phase 6: Final Verification

#### 6.1. Build Verification

```bash
# Verify the build compiles successfully
npm run build

# Run linting
npm run lint
```

**Verification checklist**:
- [ ] Build compiles successfully
- [ ] No console errors or warnings

#### 6.2. Code Quality Checks

```bash
# Run linting
npm run lint

# Run type checking
npm run type-check

# Run security audit
npm audit
```

**Verification checklist**:
- [ ] No linting errors
- [ ] No type errors
- [ ] No security vulnerabilities

#### 6.3. Manual Testing

**If applicable**:
- [ ] Test UI in browser
- [ ] Test all user interactions
- [ ] Test responsive design
- [ ] Test accessibility
- [ ] Test error states

#### 6.4. Stored Procedure Conversion Artifacts (when applicable)

If this implementation converted any stored procedures, verify all required artifacts exist:

- [ ] Conversion doc exists at `docs/conversions/{sp_name}_conversion.md` and follows the established template
- [ ] Primary service class has `Replaces stored procedure: {sp_name}.sp` in its class-level JavaDoc
- [ ] If multiple service classes: subordinate classes reference the primary via `@see`
- [ ] Dedicated mapper unit tests exist (not just indirect testing through service tests)
- [ ] All conditional branches in the SP have corresponding test cases
- [ ] v9 checklist step 20 completed: output compared against legacy SP for functional equivalence

#### 6.5. Update Task List

**Final task list update**:
- [ ] Mark all completed tasks with `[x]`
- [ ] Update progress tracking section
- [ ] Document any deviations from plan
- [ ] Add notes about any outstanding issues

## Critical Guidelines

### Domain Placement Rules

Before deciding where to place new Java classes, read the domain registry at `docs/target-architecture/domain-registry.json`.

**All new Java classes in `passage-api` MUST be placed under one of the registered domain packages in `com.williams.api.{domain}/`.** Do NOT create new top-level packages under `com.williams.api/` that are not in the registry.

Valid domain packages and their purposes are defined in the registry's `domains` array. The `allowedNonDomainPackages` array lists technical packages (like `common`) that are also valid.

**How to choose the correct domain:**
1. Look at the primary entity/table being operated on — which business domain owns that data?
2. Check the domain `description` fields in the registry for the best match
3. Follow existing code patterns — look at what's already in each domain package
4. When in doubt, follow the data: the domain that owns the primary data wins
5. Cross-cutting utilities (logging, auth, caching) belong in `common`

**Sub-domains:** Some domains have valid sub-packages (e.g., `security.contactmanager`). These are listed in the `subDomains` array of each domain entry.

### Code Quality Standards

**DO**:
- Follow existing codebase patterns and conventions
- Add meaningful comments and documentation
- Handle all error cases
- Validate all inputs
- Use TypeScript types properly
- Follow SOLID principles

**DO NOT**:
- Leave TODO comments without addressing them
- Hard-code values that should be configurable
- Ignore TypeScript errors or use `any` type unnecessarily
- Copy-paste code without understanding it
- Skip error handling

### Security Implementation

When a functional spec mentions "CHANGE permission required" or similar authorization rules:
- First verify in legacy code whether this was enforced at the API level
- If yes: implement via `@SecuredByMenuItem(ITEM_ID)` on the controller — NOT inline `hasPermission()` checks in the service
- If no: do not add security — the authorization rule describes UI menu visibility only
- **Never** hardcode func_id constants (e.g., `"ALLWIN"`, `"IT INQ"`) in service classes
- **Never** call `UserContext.hasPermission()` directly in service code for authorization
- Read `docs/target-architecture/security-architecture.md` for the complete security model

### Progress Tracking

**Task List Management**:
1. Mark task as `in_progress` in TodoWrite BEFORE starting
2. Complete the implementation work
3. Mark task as `[x]` in task-list.md when fully complete
4. Update TodoWrite to `completed`
5. Move to next task

**Task is NOT complete until**:
- [ ] Code is written and follows standards
- [ ] Documentation is updated
- [ ] Code is reviewed (self-review against implementation plan)
- [ ] No console errors or warnings

### Error Recovery

**If implementation differs from plan**:
1. Document the deviation
2. Ensure it's justified
3. Update implementation plan if needed
4. Add note to task list

**If blocked**:
1. Document the blocker in code comments
2. Mark task appropriately in TodoWrite
3. Move to another task if possible
4. Try alternative implementation approaches
5. Only report to user if ALL tasks are blocked and no progress is possible

## Task Management

**IMPORTANT: Execute autonomously. Never stop to ask for user input or present options.**

Use TodoWrite extensively AND use Task subagents to parallelize large implementations:

### Execution Strategy

For implementations with 5+ components:
1. **Main context**: Read all documents, understand requirements, create TodoWrite list
2. **Parallel Task subagents (Wave 1)**: Foundation layer (DTOs, entities, types)
3. **Parallel Task subagents (Wave 2)**: Data layer (repositories, API services)
4. **Parallel Task subagents (Wave 3)**: Business layer (services)
5. **Parallel Task subagents (Wave 4)**: API/UI layer (controllers, components)
6. **Main context**: Final verification

Each Task subagent should receive:
- Specific component specifications from the implementation plan
- File paths and naming conventions
- Reference patterns from existing codebase

### TodoWrite Structure

```
Initial Setup:
- Read task-list.md
- Read implementation-plan.md
- Read target architecture docs
- Understand existing codebase patterns
- Create comprehensive todo list matching task-list.md

Backend Implementation:
- Create DTOs for requests/responses
- Create domain entities
- Create repository interfaces and implementations
- Create service classes
- Create controllers
- Configure module

Database Changes:
- Create migration scripts
- Run migrations
- Verify rollback
- Verify database changes

Frontend Implementation (if applicable):
- Create TypeScript types
- Create API client services
- Create custom hooks
- Create React components

Documentation:
- Add code documentation
- Update API documentation
- Update architecture documentation

Final Verification:
- Check code quality
- Manual testing (if UI)
- Update task list with [x] for completed items
```

## Success Criteria

**Execution Success** (these are prerequisites for implementation success):
- [ ] Completed autonomously without asking user for input or approval
- [ ] Used Task subagents effectively to parallelize work where beneficial
- [ ] Made implementation decisions independently based on implementation plan
- [ ] Did not present options or recommendations requiring user choice

**Implementation Complete**:
- [ ] All tasks in task-list.md marked with [x]
- [ ] All code follows target architecture
- [ ] No linting or type errors
- [ ] Documentation complete and accurate
- [ ] Code reviewed against implementation plan
- [ ] Manual testing complete (if applicable)

**Code Quality**:
- [ ] Follows existing codebase conventions
- [ ] Properly handles all error cases
- [ ] Input validation comprehensive
- [ ] TypeScript types used correctly
- [ ] No console warnings or errors
- [ ] Security considerations addressed
- [ ] Performance considerations addressed

**Documentation Quality**:
- [ ] All public APIs documented
- [ ] Complex logic explained
- [ ] Architecture diagrams updated
- [ ] API documentation complete
- [ ] Examples provided where helpful

## Troubleshooting

### Type Errors

**Problem**: TypeScript compilation errors

**Solutions**:
1. Check interface/type definitions match usage
2. Ensure imports are correct
3. Verify generic types are properly specified
4. Check for missing or incorrect property types
5. Use type guards for union types
6. Avoid using `any` - define proper types

### Module Import Errors

**Problem**: Cannot resolve modules

**Solutions**:
1. Check file path is correct
2. Verify module is properly exported
3. Check tsconfig.json path mappings
4. Ensure file extension is correct
5. Verify barrel exports (index.ts) are correct

### Database Migration Issues

**Problem**: Migration fails

**Solutions**:
1. Check SQL syntax
2. Verify foreign key references exist
3. Check for naming conflicts
4. Ensure proper migration order
5. Verify database connection
6. Check for data type compatibility

### API Integration Issues

**Problem**: Frontend cannot connect to backend API

**Solutions**:
1. Verify API endpoint path is correct
2. Check CORS configuration
3. Ensure authentication headers are included
4. Verify request/response format matches
5. Check network tab in browser devtools
6. Verify backend is running and accessible

---

**End of Command Specification**
