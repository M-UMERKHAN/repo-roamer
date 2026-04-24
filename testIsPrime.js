const { isPrime } = require('./isPrime');

console.log('Testing isPrime function:');
console.log('isPrime(0):', isPrime(0)); // false
console.log('isPrime(1):', isPrime(1)); // false
console.log('isPrime(2):', isPrime(2)); // true
console.log('isPrime(3):', isPrime(3)); // true
console.log('isPrime(4):', isPrime(4)); // false
console.log('isPrime(5):', isPrime(5)); // true
console.log('isPrime(10):', isPrime(10)); // false
console.log('isPrime(13):', isPrime(13)); // true
console.log('isPrime(25):', isPrime(25)); // false
console.log('isPrime(29):', isPrime(29)); // true