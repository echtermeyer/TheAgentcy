![Agentcy Banner](src\docs\images\Agentcy.png)

## Quick Start

Before diving into the world of fully automated development of distributed web applications, make sure to follow these steps to get the *Agentcy* project up and running.

### Installation

Agentcy uses Poetry for dependency management. Ensure that you have Poetry installed before proceeding. If not, you can find the installation instructions here: [Poetry Installation](https://python-poetry.org/docs/#installation).

After installing Poetry, execute these commands in your terminal:

```bash
poetry install
```

This command will install all the necessary dependencies for the project. Once the installation is complete, you can activate the virtual environment with the following command:

```bash
poetry shell
```

Alternatively, you can run the program directly with Poetry:

```bash
poetry run python.run
```

### Configuration

Create a `.env` file in the root directory of the project to store your OpenAI key and organization:

```env
OPENAI_ORG=your-organization
OPENAI_API_KEY=your-openai-key
```

Please replace `your-openai-key` and `your-organization` with your actual OpenAI API key and organization details.

### Docker Daemon

Ensure that the Docker Daemon is running on your host machine since *Agentcy* utilizes containerization for some of its functions. 

## If Everything Works...

![Chatbox Photo](src\docs\images\Chatbox.png)

If the installation and configuration were successful, a chat window similar to the one shown above should appear when you start the program.

## Architecture

The Chat Architecture is implemented accordingly to the following showcase. (In German)

![Chat Architecture](src\docs\images\Architecture.png)

The project leverages a specialized architecture that assigns distinct roles to LLM-Agents, streamlining the development lifecycle:

- **Orchestrator**: Serves as the product owner, initiating the development process by translating user requirements into tasks for the agents.
- **Developer & Tester**: Collaboratively work to design, test, and refine the asigned schema ensuring accuracy and efficiency.
- **Documentor**: Creates comprehensive documentation based on the final, optimized code to support further development and maintenance.

This setup emphasizes iterative development, inter-agent communication, and thorough documentation for an integrated and error-corrected software development process.

## Advanced Technology Architecture

*Agentcy* differentiates itself with an architecture that not only embraces modern development practices but also leverages the power of containerization and live server capabilities:

- **Containerization**: Agentcy uses Docker to containerize components, enhancing deployment flexibility and environment consistency.
- **Live Server Environment**: Features a live server setup for real-time testing and iteration, improving development speed and quality.

These features represent a leap forward in streamlining the development process, from conception to deployment.

## Contributions

We invite the community to contribute to *Agentcy* by reporting issues, submitting pull requests, and improving the documentation. Any contribution that advances the project and makes the automation of software development more accessible is welcome.

---
