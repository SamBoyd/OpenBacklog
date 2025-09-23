import { CompletableText } from "#types";

export const jsonToText = (json: string): string => {
  const data = JSON.parse(json);
  let result = '';

  data.forEach((initiative: any) => {
    result += `-[ ] ${initiative.title}\n`;
    initiative.tasks.forEach((task: any) => {
      result += `  -[ ] ${task.title}\n`;
      task.checklist.forEach((item: any) => {
        result += `    -[ ] ${item.title}\n`;
      });
    });
  });

  return result;
};

export const textToJson = (text: string): string => {
  const lines = text.split('\n').filter(line => line.trim() !== '');
  const result: any[] = [];
  let currentInitiative: any = null;
  let currentTask: any = null;

  lines.forEach(line => {
    const trimmedLine = line.trim();
    if (trimmedLine.startsWith('-[ ]')) {
      if (line.startsWith('  ')) {
        if (line.startsWith('    ')) {
          // Checklist item
          const itemTitle = trimmedLine.slice(5).trim();
          currentTask.checklist.push({ title: itemTitle });
        } else {
          // Task
          const taskTitle = trimmedLine.slice(5).trim();
          currentTask = { title: taskTitle, checklist: [] };
          currentInitiative.tasks.push(currentTask);
        }
      } else {
        // Initiative
        const initiativeTitle = trimmedLine.slice(5).trim();
        currentInitiative = { title: initiativeTitle, tasks: [] };
        result.push(currentInitiative);
      }
    }
  });

  return JSON.stringify(result, null, 2);
};

export const validateMarkdown = (text: string): { success: boolean; error: string | null } => {
  const lines = text.split('\n').filter(line => line.trim() !== '');
  let lastInitiativeFound = false;
  let lastTaskFound = false;

  for (const line of lines) {
    const match = line.match(/^(\t*)-\[ \]\s(.+)$/);
    if (!match) {
      return { success: false, error: 'Line does not match the required "-[ ] " format or indentation' };
    }

    const indentLevel = match[1].length;
    if (indentLevel === 0) {
      lastInitiativeFound = true;
      lastTaskFound = false;
    } else if (indentLevel === 1) {
      if (!lastInitiativeFound) {
        return { success: false, error: 'Found a task before any initiative' };
      }
      lastTaskFound = true;
    } else if (indentLevel === 2) {
      if (!lastTaskFound) {
        return { success: false, error: 'Found a checklist item before any task' };
      }
    } else {
      return { success: false, error: 'Indentation level is too deep (must be 0, 1, or 2 tabs)' };
    }
  }

  return { success: true, error: null };
};

export const validateCompletableText = (items: CompletableText[]): { success: boolean; error: string | null } => {
  let lastInitiativeFound = false;
  let lastTaskFound = false;

  for (const item of items) {
    const { tabLevel } = item;

    if (tabLevel > 2) {
      return { success: false, error: 'Indentation level is too deep (must be 0, 1, or 2)' };
    }
    if (tabLevel === 0) {
      lastInitiativeFound = true;
      lastTaskFound = false;
    } else if (tabLevel === 1) {
      if (!lastInitiativeFound) {
        return { success: false, error: 'Found a task before any initiative' };
      }
      lastTaskFound = true;
    } else if (tabLevel === 2) {
      if (!lastTaskFound) {
        return { success: false, error: 'Found a checklist item before any task' };
      }
    }
  }

  return { success: true, error: null };
}
