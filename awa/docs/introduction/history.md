# History

How did we get here?

## Q1 2024: RAMROD/AIDE and Region 4

The journey started at Region 4, where a team of innovators built a purpose-built tool used to accelerate development on a project with AI agents. That system was called **RAMROD** (or Dormar, or AIDE ... naming thing is hard!). This system was very effective, and enabled the Region 4 team to deliver a seemingly impossible project in record time.

## Q3 2024: TaskStream

RAMROD was purpose-built for Region 4. It was adapted by a few other teams, but in order to widen the impact of the patterns established by RAMROD, a new tool was conceptualized called **TaskStream**.

TaskStream was built with the vision of "AI for all". It used YAML definitions to accelerate agentic workflow development, and was designed as a general-purpose tool. Experimentation was core to the development of TaskStream, and many features were piloted to aid various use cases, from MCP integration to CLI agent management.

Over the course of 2024 and H1 2025, the TaskStream core team supported many teams and individuals as they ramped up and leveraged TaskStream to deliver agentic workflows. These experiences yielded valuable learnings of both the power and the challenges of building agentic workflows as deliverables and accelerators. In late Q2 2025, as different teams ran into similar challenges, the core team began to ideate on a possible pivot of this core accelerator tooling that could more effectively accelerate our teams and enable a wider variety of use cases.

The team learned many lessons of the last few months. Here are some of the most important include:

- **Reality has a surprising amount of detail**: Workflows are not as generalizable as originally hypothesized at the start of the TaskStream project. Workflows must be heavily customized to specific project situations to get desired performance. The gap between demo and production is large. Teams need acceleration beyond the demo. Specifically, learnings from the sales cycles and implementations at Marathon, Securian, Cleveland Clinic, and Boeing all pointed to the need for a more flexible, more powerful tool of a different kind.
- **Highly complex YAML is a no-man's land**: Workflow YAMLs for realistic (not demo) use cases become too complex for non-technical users, and even highly technical users required non-trivial training to become effective. Yet at the same time, YAML is not as powerful or flexible for engineers as custom code would be &mdash; it is just too restrictive. The Configurator UI was an attempt to address this issue, but it required significant continued investment to keep it in sync with core TaskStream features. To truly reconcile these issues in TaskStream would have required a significant investment in product development that just wasn't feasible.
- **Restrictive client environments are a significant barrier**: Several teams attempting to use TaskStream ran into barriers when trying to install in their client's environment. Locked down VDIs, WSL disablement, and other security-focused restrictions made even "run a single Docker container" onboarding a non-trivial hurdle. Beyond the technical, client hesitance to adopt a "platform" complicated conversations and stalled acceleration efforts.
- **Technical debt is costly**: Some decisions made at the inception of TaskStream weighed down the project, and would have been too complex to meaningfully address. Hindsight is 20/20, and these lessons have been carried forward into AWA.
- **Friction led to slow uptake**: Despite good intentions and the hard work of the core team, TaskStream saw relatively limited uptake by project teams without direct SME core team support. This was due to a number of factors, primary of which was the high barrier to entry of installing TaskStream (locally, but especially in restrictive client environments) and training engineers on the YAML DSL and capabilities (training above and beyond generic training in problem solving with agentic workflows).
- **Acceleration is critical, and use cases are numerous**: Despite these challenges, one thing was clear: the need for acceleration in the development of agentic workflows will be critical to our teams success going forward. Both when it comes to delivering workflows as client deliverables, and leveraging workflows to accelerate all aspects of our business.

## June 2025: Pivot to AWA, and the AWA MVP

Eventually, in June 2025, the core TaskStream team finally made the decision to pivot from TaskStream itself. A new project was started, the Agentic Workflow Accelerator (AWA).

Crucially, this new tool leveraged many of the best parts of the internals of TaskStream, but wrapped them in an easier to use, more flexible package.

The team released the MVP of AWA at the start of July 2025, and are continuing to work on the [Roadmap](/introduction/roadmap) to bring more agentic workflow acceleration to our teams.
