# Test Files for Passmatic

This directory contains test files used to demonstrate and test Passmatic's functionality.

## example-typescript.ts

A comprehensive TypeScript file that includes various language features and patterns that Passmatic may ask questions about:

### Features Included:

1. **TypeScript Interfaces** - User and Post type definitions
2. **Destructuring Patterns** - Object and array destructuring in function parameters
3. **Generic Functions** - Type-constrained generic functions
4. **Async/Await** - Async functions with proper error handling
5. **Memoization** - Higher-order function using Map for caching
6. **Function Overloads** - TypeScript function overloading
7. **Class Design** - Private fields, accessors, and generators
8. **Spread Operators** - Object spread for immutability
9. **Type Guards** - Type narrowing and checking
10. **Complex Types** - Union types and optional parameters

### How to Test

1. Make changes to any part of this file
2. Create a pull request
3. Passmatic will analyze your diff and generate **3 relevant questions**
4. Respond with:
   ```
   !answer
   1. Your answer to question 1
   2. Your answer to question 2
   3. Your answer to question 3
   ```
   to validate

### Example Questions Passmatic May Ask

- Why did you use destructuring in the function signature instead of passing the entire object?
- What's the purpose of the generic constraint in the `findItem` function?
- How does the memoization implementation handle different argument types?
- Why is the `PostManager` class using a generator for iteration?
- What edge cases does your async error handling cover?

### Adding More Tests

Feel free to add more test files with different languages and patterns:

- **test-go.go** - Go examples with pointers, goroutines, channels
- **test-rust.rs** - Rust examples with ownership, borrowing, lifetimes
- **test-cpp.cpp** - C++ examples with pointers, memory management
- **test-react.tsx** - React hooks and component patterns
- **test-api.ts** - API integration and error handling

Remember: Passmatic focuses on the code you actually changed, not the entire file!
