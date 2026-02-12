/*  Task-CLI: TCP client for the Advanced Networking course.
    Connects to adnet-agent, sends "TASK-CLI <keyword>", reads all response data,
    and reports total bytes received, last 8 characters, and transfer duration.

    Usage: cargo run -- <keyword>
*/

use std::{
    env,
    io::{self, Read, Write},
    net::TcpStream,
    process,
    time::Instant,
};

const SERVER_ADDR: &str = "10.0.0.3:12345";
const BUF_SIZE: usize = 8192;

fn main() {
    // Parse keyword from CLI arguments
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <keyword>", args[0]);
        process::exit(1);
    }
    let keyword = &args[1];

    println!("Task-CLI starting");
    println!("Connecting to {}...", SERVER_ADDR);

    // Open TCP connection to adnet-agent server
    let mut stream = match TcpStream::connect(SERVER_ADDR) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("Failed to connect to {}: {}", SERVER_ADDR, e);
            process::exit(1);
        }
    };

    println!("Connected.");

    // Send control message: "TASK-CLI keyword"
    let command = format!("TASK-CLI {}", keyword);
    if let Err(e) = stream.write_all(command.as_bytes()) {
        eprintln!("Failed to send command: {}", e);
        process::exit(1);
    }
    println!("Sent command: {}", command);

    // Start clock to measure transfer duration
    let start = Instant::now();

    // Read all data until server closes connection
    let mut buf = [0u8; BUF_SIZE];
    let mut total_bytes: usize = 0;
    let mut last_8 = String::new();

    loop {
        match stream.read(&mut buf) {
            Ok(0) => {
                // Server closed the connection
                break;
            }
            Ok(n) => {
                total_bytes += n;

                // Maintain the last 8 characters received
                let chunk = String::from_utf8_lossy(&buf[..n]);
                last_8.push_str(&chunk);
                if last_8.len() > 8 {
                    let excess = last_8.len() - 8;
                    last_8 = last_8[excess..].to_string();
                }
            }
            Err(ref e) if e.kind() == io::ErrorKind::Interrupted => {
                // Retry on EINTR
                continue;
            }
            Err(e) => {
                eprintln!("Read error: {}", e);
                process::exit(1);
            }
        }
    }

    let duration = start.elapsed();

    println!("--- Results ---");
    println!("Total bytes received: {}", total_bytes);
    println!("Last 8 characters:    {}", last_8);
    println!(
        "Transfer duration:    {}.{:03} seconds",
        duration.as_secs(),
        duration.subsec_millis()
    );
}