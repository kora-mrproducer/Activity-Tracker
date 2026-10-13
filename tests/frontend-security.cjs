const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const results = {innerHTML: ''};
const toasts = {setAttribute() {}, appendChild(node) {this.last = node;}};
const document = {
    documentElement: {}, addEventListener() {},
    getElementById(id) {return id === 'searchResults' ? results : id === 'toast-container' ? toasts : null;},
    createElement() {return {setAttribute() {}, classList: {add() {}}, remove() {}};}
};
const context = {document, setTimeout() {}, console};
context.window = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync('static/js/common.js', 'utf8'), context);
const payload = '<img src=x onerror="alert(1)">';
context.displaySearchResults([{id: 1, desc: payload, source: payload, priority: payload, start_date: payload}]);
assert(!results.innerHTML.includes('<img'));
assert(results.innerHTML.includes('&lt;img'));
context.showToast(payload, 'info');
assert(!toasts.last.innerHTML.includes('<img'));
assert(toasts.last.innerHTML.includes('&lt;img'));
console.log('Stored XSS regression checks passed');
