/*  Task-SRV: TCP server for the Advanced Networking course.
    Listens for connections from adnet-agent, reads 5-byte requests
    (4-byte u32 byte count + 1-byte fill character), and writes
    the requested number of bytes back.

    Usage: cargo run -- <keyword>
*/

use std::{
    env,
    io::{self, Read, Write},
    net::{TcpListener, TcpStream},
    process,
    thread,
};

const AGENT_ADDR: &str = "10.0.0.3:12345";
const LISTEN_ADDR: &str = "0.0.0.0:12321";
const MY_IP: &str = "10.0.0.1";
const MY_PORT: u16 = 12321;
const BUF_SIZE: usize = 8192;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <keyword>", args[0]);
        process::exit(1);
    }
    let keyword = &args[1];

    println!("Task-SRV starting");

    // Bind listening socket
    let listener = TcpListener::bind(LISTEN_ADDR).unwrap_or_else(|e| {
        eprintln!("Failed to bind {}: {}", LISTEN_ADDR, e);
        process::exit(1);
    });
    println!("Listening on {}", LISTEN_ADDR);

    // Send control message to adnet-agent
    let mut agent = TcpStream::connect(AGENT_ADDR).unwrap_or_else(|e| {
        eprintln!("Failed to connect to {}: {}", AGENT_ADDR, e);
        process::exit(1);
    });
    let command = format!("TASK-SRV {} {}:{}", keyword, MY_IP, MY_PORT);
    agent.write_all(command.as_bytes()).unwrap_or_else(|e| {
        eprintln!("Failed to send command: {}", e);
        process::exit(1);
    });
    println!("Sent: {}", command);

    // Accept connections and spawn a thread per client
    for stream in listener.incoming() {
        match stream {
            Ok(socket) => {
                let addr = socket.peer_addr().unwrap();
                println!("Accepted connection from {}", addr);
                thread::spawn(move || {
                    process_client(socket);
                });
            }
            Err(e) => {
                eprintln!("Accept error: {}", e);
            }
        }
    }
}

fn process_client(mut socket: TcpStream) {
    loop {
        // Read 5-byte request: 4-byte u32 (big-endian) byte count + 1-byte fill
        let mut header = [0u8; 5];
        if read_exact(&mut socket, &mut header).is_err() {
            return;
        }

        let total = u32::from_be_bytes([header[0], header[1], header[2], header[3]]);
        let character = header[4];

        // Write `total` bytes filled with `character`
        let fill = vec![character; BUF_SIZE.min(total as usize)];
        let mut written: u32 = 0;
        while written < total {
            let remaining = (total - written) as usize;
            let chunk = remaining.min(fill.len());
            match socket.write(&fill[..chunk]) {
                Ok(n) => written += n as u32,
                Err(e) => {
                    eprintln!("Write error: {}", e);
                    return;
                }
            }
        }

        println!("Wrote {} bytes of byte {}", total, character);
    }
}

fn read_exact(stream: &mut TcpStream, buf: &mut [u8]) -> Result<(), io::Error> {
    let mut pos = 0;
    while pos < buf.len() {
        match stream.read(&mut buf[pos..]) {
            Ok(0) => return Err(io::Error::new(io::ErrorKind::UnexpectedEof, "closed")),
            Ok(n) => pos += n,
            Err(ref e) if e.kind() == io::ErrorKind::Interrupted => continue,
            Err(e) => return Err(e),
        }
    }
    Ok(())
}
