import { useReducer, useCallback, useRef } from 'react';
import { streamQuery } from '../api/sse';

const initialAgentState = { status: 'idle', events: [] };

const initialState = {
  agents: {
    Retriever: { ...initialAgentState },
    'Web Researcher': { ...initialAgentState },
    Synthesizer: { ...initialAgentState },
  },
  answer: '',
  sources: [],
  isStreaming: false,
  error: null,
};

function reducer(state, action) {
  switch (action.type) {
    case 'START':
      return { ...initialState, isStreaming: true };

    case 'AGENT_EVENT': {
      const { agent, status, message, data } = action.payload;
      if (!state.agents[agent]) return state;

      const agentState = state.agents[agent];
      const newEvents = [...agentState.events, { status, message, time: Date.now() }];

      let newAnswer = state.answer;
      let newSources = state.sources;

      // Token streaming from Synthesizer
      if (data?.type === 'token') {
        newAnswer = state.answer + message;
      }

      // Collect sources from done events
      if (status === 'done' && data?.result) {
        const result = data.result;
        if (result.sources) {
          newSources = [...state.sources, ...result.sources];
        }
        if (agent === 'Synthesizer' && result.content) {
          newAnswer = result.content;
        }
      }

      return {
        ...state,
        answer: newAnswer,
        sources: newSources,
        agents: {
          ...state.agents,
          [agent]: { status, events: newEvents },
        },
      };
    }

    case 'DONE': {
      // Deduplicate sources
      const seen = new Set();
      const unique = state.sources.filter((s) => {
        const key = s.url || s.title || '';
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      return { ...state, isStreaming: false, sources: unique };
    }

    case 'ERROR':
      return { ...state, isStreaming: false, error: action.payload };

    default:
      return state;
  }
}

export function useSSEQuery() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const abortRef = useRef(false);

  const runQuery = useCallback((query) => {
    abortRef.current = false;
    dispatch({ type: 'START' });

    streamQuery(
      query,
      (event) => {
        if (!abortRef.current) {
          dispatch({ type: 'AGENT_EVENT', payload: event });
        }
      },
      () => dispatch({ type: 'DONE' }),
      (err) => dispatch({ type: 'ERROR', payload: err.message }),
    );
  }, []);

  return { ...state, runQuery };
}
