import AgentPanel from './AgentPanel';

const agentNames = ['Retriever', 'Web Researcher', 'Synthesizer'];

export default function AgentPanelGrid({ agents, isActive }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {agentNames.map((name) => (
        <AgentPanel
          key={name}
          name={name}
          agentState={agents[name]}
          isActive={isActive}
        />
      ))}
    </div>
  );
}
