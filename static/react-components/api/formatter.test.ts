import { describe, it, expect } from 'vitest';
import { jsonToText, textToJson, validateMarkdown, validateCompletableText } from './formatter';

describe.skip('jsonToText', () => {
  it('should convert JSON to text format', () => {
    const json = JSON.stringify([
      {
        title: 'Initiative 1',
        tasks: [
          {
            title: 'Task 1',
            checklist: [
              { title: 'Item 1' },
              { title: 'Item 2' }
            ]
          },
          {
            title: 'Task 2',
            checklist: []
          }
        ]
      },
      {
        title: 'Initiative 2',
        tasks: []
      }
    ]);

    const expectedText = `-[ ] Initiative 1\n  -[ ] Task 1\n    -[ ] Item 1\n    -[ ] Item 2\n  -[ ] Task 2\n-[ ] Initiative 2\n`;
    expect(jsonToText(json)).toBe(expectedText);
  });

  it('should handle empty JSON array', () => {
    const json = JSON.stringify([]);
    const expectedText = '';
    expect(jsonToText(json)).toBe(expectedText);
  });

  it('should handle initiatives without tasks', () => {
    const json = JSON.stringify([
      {
        title: 'Initiative 1',
        tasks: []
      }
    ]);

    const expectedText = `-[ ] Initiative 1\n`;
    expect(jsonToText(json)).toBe(expectedText);
  });

  it('should handle tasks without checklist items', () => {
    const json = JSON.stringify([
      {
        title: 'Initiative 1',
        tasks: [
          {
            title: 'Task 1',
            checklist: []
          }
        ]
      }
    ]);

    const expectedText = `-[ ] Initiative 1\n  -[ ] Task 1\n`;
    expect(jsonToText(json)).toBe(expectedText);
  });
});

describe.skip('textToJson', () => {
  it('should convert text format to JSON', () => {
    const text = `-[ ] Initiative 1\n  -[ ] Task 1\n    -[ ] Item 1\n    -[ ] Item 2\n  -[ ] Task 2\n-[ ] Initiative 2\n`;
    const expectedJson = JSON.stringify([
      {
        title: 'Initiative 1',
        tasks: [
          {
            title: 'Task 1',
            checklist: [
              { title: 'Item 1' },
              { title: 'Item 2' }
            ]
          },
          {
            title: 'Task 2',
            checklist: []
          }
        ]
      },
      {
        title: 'Initiative 2',
        tasks: []
      }
    ], null, 2);
    expect(textToJson(text)).toBe(expectedJson);
  });

  it('should handle empty text', () => {
    const text = '';
    const expectedJson = JSON.stringify([], null, 2);
    expect(textToJson(text)).toBe(expectedJson);
  });

  it('should handle initiatives without tasks', () => {
    const text = `-[ ] Initiative 1\n`;
    const expectedJson = JSON.stringify([
      {
        title: 'Initiative 1',
        tasks: []
      }
    ], null, 2);
    expect(textToJson(text)).toBe(expectedJson);
  });

  it('should handle tasks without checklist items', () => {
    const text = `-[ ] Initiative 1\n  -[ ] Task 1\n`;
    const expectedJson = JSON.stringify([
      {
        title: 'Initiative 1',
        tasks: [
          {
            title: 'Task 1',
            checklist: []
          }
        ]
      }
    ], null, 2);
    expect(textToJson(text)).toBe(expectedJson);
  });
});

describe.skip('validateMarkdown', () => {
  it('should return success for valid markdown', () => {
    const validText = `-[ ] Initiative 1\n\t-[ ] Task 1\n\t\t-[ ] Checklist Item 1\n\t-[ ] Task 2\n-[ ] Initiative 2\n`;
    const result = validateMarkdown(validText);
    expect(result.success).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should fail if line does not match the "-[ ] " pattern', () => {
    const invalidText = `-[X] Initiative 1\n`;
    const result = validateMarkdown(invalidText);
    expect(result.success).toBe(false);
    expect(result.error).toMatch(/Line does not match/);
  });

  it('should fail if a task is found before any initiative', () => {
    const invalidText = `\t-[ ] Task 1\n`;
    const result = validateMarkdown(invalidText);
    expect(result.success).toBe(false);
    expect(result.error).toMatch(/Found a task before any initiative/);
  });

  it('should fail if a checklist item is found before any task', () => {
    const invalidText = `-[ ] Initiative 1\n\t\t-[ ] Checklist Item\n`;
    const result = validateMarkdown(invalidText);
    expect(result.success).toBe(false);
    expect(result.error).toMatch(/Found a checklist item before any task/);
  });

  it('should fail if indentation level is too deep', () => {
    const invalidText = `\t\t\t-[ ] Too deep\n`;
    const result = validateMarkdown(invalidText);
    expect(result.success).toBe(false);
    expect(result.error).toMatch(/Indentation level is too deep/);
  });
});

describe.skip('validateCompletableText', () => {
  it('should return success for valid sequence', () => {
    const items = [
      { title: 'Initiative 1', isCompleted: false, tabLevel: 0, originalTabLevel: 0 },
      { title: 'Task 1', isCompleted: false, tabLevel: 1, originalTabLevel: 1 },
      { title: 'Checklist 1', isCompleted: false, tabLevel: 2, originalTabLevel: 2 },
    ];
    const result = validateCompletableText(items);
    expect(result.success).toBe(true);
    expect(result.error).toBeNull();
  });

  it('should fail if task is before initiative', () => {
    const items = [
      { title: 'Task 1', isCompleted: false, tabLevel: 1, originalTabLevel: 1 },
    ];
    const result = validateCompletableText(items);
    expect(result.success).toBe(false);
    expect(result.error).toMatch(/Found a task before any initiative/);
  });

  it('should fail if checklist item is before any task', () => {
    const items = [
      { title: 'Initiative 1', isCompleted: false, tabLevel: 0, originalTabLevel: 0 },
      { title: 'Checklist 1', isCompleted: false, tabLevel: 2, originalTabLevel: 2 }
    ];
    const result = validateCompletableText(items);
    expect(result.success).toBe(false);
    expect(result.error).toMatch(/Found a checklist item before any task/);
  });

  it('should fail if tabLevel is deeper than 2', () => {
    const items = [
      { title: 'Initiative 1', isCompleted: false, tabLevel: 0, originalTabLevel: 0 },
      { title: 'Task 1', isCompleted: false, tabLevel: 3, originalTabLevel: 3 }
    ];
    const result = validateCompletableText(items);
    expect(result.success).toBe(false);
    expect(result.error).toMatch(/Indentation level is too deep/);
  });
});
