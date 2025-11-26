import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.Pipe;
import java.util.Scanner;
import java.util.concurrent.*;   //CompletableFuture саме звідси
import java.util.concurrent.atomic.AtomicBoolean;

public class ComputationSystem {

    private static final int TIMEOUT_SECONDS = 10; //загальний тайм-аут
    private static final int X_ARGUMENT = 5;       //аргумент для функцій

    public static void main(String[] args) throws IOException {
        System.out.println("[Manager] System started. Calculating for x = " + X_ARGUMENT);
        System.out.println("[Manager] Press 'q' and Enter to stop calculation manually.");

        // 1) канали зв'язку (Java NIO Pipes)
        Pipe pipe1 = Pipe.open();
        Pipe pipe2 = Pipe.open();

        // 2) визначення задач
        //f(x) = x*2
        ComputationTask task1 = new ComputationTask("Function_1", X_ARGUMENT, pipe1.sink(), 2000);
        //f(x) = x*x (+імітація зависання для тесту скасування)
        ComputationTask task2 = new ComputationTask("Function_2", X_ARGUMENT, pipe2.sink(), 7000);

        // 3) асинхронний запуск через CompletableFuture
        CompletableFuture<Void> future1 = CompletableFuture.runAsync(task1);
        CompletableFuture<Void> future2 = CompletableFuture.runAsync(task2);

        // 4) input listener/daemon thread (для скасування)
        AtomicBoolean stopRequested = new AtomicBoolean(false);
        Thread inputListener = new Thread(() -> {
            @SuppressWarnings("resource")
            Scanner scanner = new Scanner(System.in);
            while (!Thread.currentThread().isInterrupted()) {
                if (scanner.hasNextLine()) {
                    String line = scanner.nextLine();
                    if (line.trim().equalsIgnoreCase("q")) {
                        stopRequested.set(true);
                        break;
                    }
                }
            }
        });
        inputListener.setDaemon(true);
        inputListener.start();

        // 5) головний цикл (manager loop)
        long startTime = System.currentTimeMillis();
        boolean finished = false;

        try {
            while (!finished) {
                // 1) пкревірка тайм-ауту
                if ((System.currentTimeMillis() - startTime) > TIMEOUT_SECONDS * 1000) {
                    System.out.println("\n[Manager] TIMEOUT EXCEEDED! Cancelling tasks...");
                    future1.cancel(true);
                    future2.cancel(true);
                    break;
                }

                // 2) перевірка запиту користувача на зупинку (комб q + enter)
                if (stopRequested.get()) {
                    System.out.print("\n[Manager] Stop requested. Confirm cancellation? (y/n): ");
                    @SuppressWarnings("resource")
                    Scanner confirmScanner = new Scanner(System.in);
                    String confirm = confirmScanner.nextLine();
                    if (confirm.equalsIgnoreCase("y")) {
                        System.out.println("[Manager] Cancelled by user.");
                        future1.cancel(true);
                        future2.cancel(true);
                        break;
                    } else {
                        System.out.println("[Manager] Resuming...");
                        stopRequested.set(false);
                    }
                }
                // 3) чи всі задачі виконані
                if (future1.isDone() && future2.isDone()) {
                    finished = true;
                }
                Thread.sleep(100);   //для уникнення busy-wait
            }

            //збір та обробка результатів
            System.out.println("\n--- FINAL RESULTS ---");
            Double res1 = readResultFromPipe(pipe1.source(), future1, "Function_1");
            Double res2 = readResultFromPipe(pipe2.source(), future2, "Function_2");

            if (res1 != null && res2 != null) {
                double finalResult = res1 * res2;  // бінарна операція
                System.out.printf("[Manager] SUCCESS. Result: %.2f * %.2f = %.2f%n", res1, res2, finalResult);
            } else {
                System.out.println("[Manager] CALCULATION FAILED. Result is Undefined.");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    //допоміжний метод для читання з Pipe ---
    private static Double readResultFromPipe(Pipe.SourceChannel source, CompletableFuture<Void> future, String name) {
        if (future.isCancelled()) {
            System.out.println("[" + name + "] Status: CANCELLED (No result)");
            return null;
        } else if (future.isCompletedExceptionally()) {
            System.out.println("[" + name + "] Status: ERROR (Exception occurred)");
            return null;
        }

        //якщо задача успішна, читаємо з Pipe
        ByteBuffer buffer = ByteBuffer.allocate(8); //8 байт
        try {
            int bytesRead = source.read(buffer);
            if (bytesRead != -1) {
                buffer.flip(); //пкремикаємо режим буфера на читання
                double val = buffer.getDouble();
                System.out.println("[" + name + "] Status: OK. Value: " + val);
                return val;
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        System.out.println("[" + name + "] Status: ERROR (Pipe empty)");
        return null;
    }

    // внутрішній клас задачі 
    // Task/Process
    static class ComputationTask implements Runnable {
        private final String name;
        private final int x;
        private final Pipe.SinkChannel sink;
        private final int delayMs;

        public ComputationTask(String name, int x, Pipe.SinkChannel sink, int delayMs) {
            this.name = name;
            this.x = x;
            this.sink = sink;
            this.delayMs = delayMs;
        }

        @Override
        public void run() {
            try {
                System.out.println("   -> " + name + " started...");
                
                Thread.sleep(delayMs); //імітація обчислень

                //перевірка на переривання
                if (Thread.currentThread().isInterrupted()) return;

                double result;           //обчислення
                if (name.equals("Function_1")) {
                    result = x * 2.0; 
                } else {
                    result = x * x * 1.0;
                }

                //запис результату в Pipe
                ByteBuffer buffer = ByteBuffer.allocate(8);
                buffer.putDouble(result);
                buffer.flip();
                
                while (buffer.hasRemaining()) {
                    sink.write(buffer);
                }
                // sink.close();
                
                System.out.println("   -> " + name + " finished calculation.");

            } catch (InterruptedException e) {
                System.out.println("   -> " + name + " was INTERRUPTED.");
            } catch (IOException e) {
                System.out.println("   -> " + name + " IO Error: " + e.getMessage());
            }
        }
    }
}