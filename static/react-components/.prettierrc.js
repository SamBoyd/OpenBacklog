const { tab } = require('@testing-library/user-event/dist/cjs/convenience/tab.js');

module.exports = {
  ...require('gts/.prettierrc.json'),
  // Add any additional Prettier settings here
  tabWidth: 4,
  newline: 'auto',
  emptyLines: 1,
}
