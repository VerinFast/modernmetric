// Sample Retool ToolScript file
function MainToolScript() {
  const data = useData();
  
  return (
    <Container>
      <Text value="Hello Retool!" />
      <Table 
        data={data.users}
        onRowSelect={(row) => {
          showNotification('Selected: ' + row.name);
        }}
      />
      <Button
        label="Refresh"
        onClick={() => {
          queries.fetchUsers.run();
        }}
      />
    </Container>
  );
}
