/**
 * Test file for Passmatic PR testing
 * This file contains various TypeScript features for testing
 */

interface User {
  id: number;
  name: string;
  email: string;
  roles: string[];
}

interface Post {
  id: number;
  title: string;
  content: string;
  author: User;
  tags: string[];
  createdAt: Date;
}

const users: User[] = [
  {
    id: 1,
    name: "John Doe",
    email: "john@example.com",
    roles: ["admin", "editor"]
  },
  {
    id: 2,
    name: "Jane Smith",
    email: "jane@example.com",
    roles: ["editor"]
  }
];

const posts: Post[] = [
  {
    id: 1,
    title: "Introduction to TypeScript",
    content: "TypeScript is a typed superset of JavaScript...",
    author: users[0],
    tags: ["typescript", "tutorial"],
    createdAt: new Date("2024-01-15")
  },
  {
    id: 2,
    title: "Advanced Destructuring Patterns",
    content: "Destructuring allows you to extract values from arrays...",
    author: users[1],
    tags: ["javascript", "destructuring"],
    createdAt: new Date("2024-02-20")
  }
];

// Advanced destructuring example
function processPost({ id, title, author: { name, roles: [primaryRole, ...otherRoles] } }: Post): string {
  console.log(`Processing post #${id}: ${title}`);
  console.log(`Author: ${name} (${primaryRole})`);
  console.log(`Additional roles: ${otherRoles.join(", ")}`);
  
  return `Post #${id} processed successfully`;
}

// Generic function with constraints
function findItem<T extends { id: number }>(items: T[], id: number): T | undefined {
  return items.find(item => item.id === id);
}

// Async function with proper error handling
async function fetchPostDetails(postId: number): Promise<Post | null> {
  try {
    const post = findItem(posts, postId);
    
    if (!post) {
      console.warn(`Post #${postId} not found`);
      return null;
    }
    
    // Simulate async operation
    await new Promise(resolve => setTimeout(resolve, 100));
    
    return post;
  } catch (error) {
    console.error("Error fetching post:", error);
    return null;
  }
}

// Memoization example using Map
const memoCache = new Map<string, any>();

function memoize<T extends (...args: any[]) => any>(fn: T): T {
  return ((...args: any[]) => {
    const key = JSON.stringify(args);
    
    if (memoCache.has(key)) {
      return memoCache.get(key);
    }
    
    const result = fn(...args);
    memoCache.set(key, result);
    
    return result;
  }) as T;
}

// Using memoization
const expensiveOperation = memoize((n: number): number => {
  console.log(`Computing fib(${n})...`);
  if (n <= 1) return n;
  return expensiveOperation(n - 1) + expensiveOperation(n - 2);
});

// Function overloads
function processData(input: string): string;
function processData(input: number): number;
function processData(input: string | number): string | number {
  if (typeof input === "string") {
    return input.toUpperCase();
  }
  return input * 2;
}

// Class with private fields and accessors
class PostManager {
  private _posts: Post[] = [];
  
  get posts(): Post[] {
    return [...this._posts];
  }
  
  addPost(post: Post): void {
    this._posts.push(post);
  }
  
  findPostsByTag(tag: string): Post[] {
    return this._posts.filter(post => post.tags.includes(tag));
  }
  
  *[Symbol.iterator](): Iterator<Post> {
    for (const post of this._posts) {
      yield post;
    }
  }
}

const manager = new PostManager();
posts.forEach(post => manager.addPost(post));

console.log(processPost(posts[0]));
console.log(processData("hello"));
console.log(processData(21));
console.log(expensiveOperation(10));

// Example of using spread operator with objects
const updatedUser = {
  ...users[0],
  name: "John Updated",
  email: "john.updated@example.com"
};

console.log("Updated user:", updatedUser);
