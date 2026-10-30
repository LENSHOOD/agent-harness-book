// Runs the actual Pi 1.4.0 loop with a scripted provider; no model service or credentials.
import assert from 'node:assert/strict';
import test from 'node:test';
import { runAgentLoop } from '@earendil-works/pi-agent-core';
import { createAssistantMessageEventStream } from '@earendil-works/pi-ai';

const model = {
  id: 'book-scripted-provider', name: 'Book scripted provider',
  api: 'openai-responses', provider: 'openai', baseUrl: 'https://example.invalid',
  reasoning: false, input: ['text'], contextWindow: 8192, maxTokens: 2048,
  cost: {input: 0, output: 0, cacheRead: 0, cacheWrite: 0},
};
const user = content => ({role: 'user', content, timestamp: 0});
const call = (id, args = {value: 3}) => ({type: 'toolCall', id, name: 'double', arguments: args});
const answer = (content, stopReason = 'stop') => ({
  role: 'assistant', content, stopReason, api: model.api,
  provider: model.provider, model: model.id, timestamp: 0,
  usage: {input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0,
    cost: {input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0}},
});
const final = () => answer([{type: 'text', text: 'done'}]);
const result = (value, terminate = false) => ({
  content: [{type: 'text', text: String(value)}], details: {value}, terminate,
});

async function exercise(responses, {config = {}, execute, history = []} = {}) {
  const requests = [], events = [], executions = [];
  const tool = {
    name: 'double', label: 'Double', description: 'Double an integer in memory.',
    parameters: {type: 'object', properties: {value: {type: 'integer'}}, required: ['value']},
    execute: async (id, args) => {
      executions.push(id);
      return execute ? execute(id, args) : result(args.value * 2);
    },
  };
  const streamFn = (_model, context) => {
    requests.push(structuredClone(context));
    const next = responses[requests.length - 1];
    assert.ok(next, 'Unexpected additional model call');
    const stream = createAssistantMessageEventStream();
    queueMicrotask(() => stream.push(next.stopReason === 'error' || next.stopReason === 'aborted'
      ? {type: 'error', reason: next.stopReason, error: next}
      : {type: 'done', reason: next.stopReason, message: next}));
    return stream;
  };
  const messages = await runAgentLoop([user('start')], {messages: history, tools: [tool]}, {
    model, convertToLlm: messages => messages, ...config,
  }, event => {events.push(structuredClone(event));}, undefined, streamFn);
  return {requests, events, executions, messages};
}

test('a real tool result reaches the next provider request and the loop ends', async () => {
  const run = await exercise([answer([call('one')], 'toolUse'), final()]);
  assert.deepEqual(run.executions, ['one']);
  assert.equal(run.requests.length, 2);
  assert.equal(run.requests[1].messages.find(m => m.role === 'toolResult').content[0].text, '6');
  assert.equal(run.events.at(-1).type, 'agent_end');
});

test('request projection removes UI-only messages without deleting original history', async () => {
  const history = [{role: 'ui_note', content: 'never send', timestamp: 0}];
  const order = [];
  const run = await exercise([final()], {history, config: {
    transformContext: async messages => {order.push('transform'); return messages.filter(m => m.role !== 'ui_note');},
    convertToLlm: messages => {order.push('convert'); return messages;},
  }});
  assert.deepEqual(order, ['transform', 'convert']);
  assert.ok(run.requests[0].messages.every(m => m.role !== 'ui_note'));
  assert.equal(history[0].role, 'ui_note');
});

test('invalid arguments become tool errors without invoking the tool', async () => {
  const run = await exercise([answer([call('bad', {})], 'toolUse'), final()]);
  assert.deepEqual(run.executions, []);
  assert.equal(run.messages.find(m => m.role === 'toolResult').isError, true);
});

test('truncated model output cannot execute even a syntactically valid tool call', async () => {
  const run = await exercise([answer([call('truncated')], 'length'), final()]);
  assert.deepEqual(run.executions, []);
  assert.equal(run.messages.find(m => m.role === 'toolResult').isError, true);
});

test('an execution failure is returned as feedback, not silently treated as success', async () => {
  const run = await exercise([answer([call('fails')], 'toolUse'), final()], {
    execute: () => {throw new Error('synthetic storage failure');},
  });
  const failure = run.requests[1].messages.find(m => m.role === 'toolResult');
  assert.equal(failure.isError, true);
  assert.match(failure.content[0].text, /synthetic storage failure/);
});

test('follow-up work starts another turn after an otherwise final response', async () => {
  let polled = false;
  const run = await exercise([final(), final()], {config: {
    getFollowUpMessages: async () => {
      if (polled) return [];
      polled = true;
      return [user('queued follow-up')];
    },
  }});
  assert.equal(run.requests.length, 2);
  assert.equal(run.requests[1].messages.at(-1).content, 'queued follow-up');
});

test('one terminating tool cannot suppress feedback for a mixed tool batch', async () => {
  const run = await exercise([answer([call('terminate'), call('continue')], 'toolUse'), final()], {
    execute: id => result(id, id === 'terminate'),
  });
  assert.equal(run.requests.length, 2);
  assert.equal(run.requests[1].messages.filter(m => m.role === 'toolResult').length, 2);
});

test('all terminating results can stop before another provider request', async () => {
  const run = await exercise([answer([call('terminate-a'), call('terminate-b')], 'toolUse')], {
    execute: () => result('finished by tool', true),
  });
  assert.equal(run.executions.length, 2);
  assert.equal(run.requests.length, 1);
  assert.equal(run.events.at(-1).type, 'agent_end');
});

test('a provider abort ends the low-level run and does not execute attached calls', async () => {
  const run = await exercise([answer([call('must-not-run')], 'aborted')]);
  assert.deepEqual(run.executions, []);
  assert.equal(run.requests.length, 1);
  assert.equal(run.events.at(-1).type, 'agent_end');
});
