# Java 21 unified build

- All JVM modules (CLI, Java agent, desktop UI) use the shared JDK 21 toolchain.
- Kotlin emits JVM 21 bytecode; Java compilation uses --release 21.
- GitHub Actions installs only Temurin 21, then runs Gradle test installDist.
- Windows/Linux native jobs already use JDK 21 headers; native C++17 and JNI/JVMTI API versions remain unchanged.
- doctor now requires Java 21 or newer; setup messages and current usage documentation are updated.
- Recovery and bytecode reconstruction logic are unchanged. Reconstructed target class versions still follow the original input.

## Validation

Passed: Java version diagnostic checks for 8/17/20/21, JAVA_HOME warning behavior, Python syntax checks, shell setup syntax, workflow YAML parsing and Java version assertions, common Java/Kotlin target assertions, original-file preservation and ZIP integrity.

Full Gradle build and JVM tests could not run locally: only JDK 17 is installed and the environment cannot download the Gradle distribution. The GitHub Actions workflow will run JVM tests on JDK 21 before packaging. This ZIP contains the modified source project, not newly compiled binaries.
